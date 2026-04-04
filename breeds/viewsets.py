import csv
import io
import ipaddress
import socket
import urllib.error
import urllib.request
from urllib.parse import urlparse

from django.conf import settings as django_settings
from django.db import DatabaseError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db import transaction

from .models import Breed
from .serializers import BreedSerializer, BreedMatchRequestSerializer


def _parse_breed_csv_rating(value):
    """Same rules as import_dogdb_csv: 1–10 as-is; 11–100 → 1–10 scale."""
    if value is None or str(value).strip() == "":
        return None
    try:
        raw = int(round(float(str(value).strip())))
    except (ValueError, TypeError):
        return None
    if raw <= 0:
        return None
    if raw <= 10:
        return raw
    if raw <= 100:
        return max(1, min(10, round(raw / 10.0)))
    return 10


_BREED_GROUP_MAP = {
    "Gundog": "Gundog",
    "Hound": "Hound",
    "Pastoral": "Pastoral",
    "Terrier": "Terrier",
    "Toy": "Toy",
    "Utility": "Utility",
    "Working": "Working",
    "Crossbreed": "Crossbreed",
    "Pure": "Pure",
}

_BREED_SIZE_MAP = {
    "XS": "XS",
    "S": "S",
    "M": "M",
    "L": "L",
    "XL": "XL",
    "x-small": "XS",
    "small": "S",
    "medium": "M",
    "large": "L",
    "x-large": "XL",
}


def _valid_breed_groups():
    return {c[0] for c in Breed._meta.get_field("group").choices}


def _valid_breed_sizes():
    return {c[0] for c in Breed._meta.get_field("size").choices}


def _csv_column_map(fieldnames):
    """
    Map header lookups (exact + casefold) -> DictReader key on each row.
    Strips whitespace and leading BOM so Excel/UTF-8 exports still match.
    """
    m = {}
    for fn in fieldnames or []:
        if fn is None:
            continue
        logical = fn.strip().lstrip("\ufeff")
        if not logical:
            continue
        if logical not in m:
            m[logical] = fn
        cf = logical.casefold()
        if cf not in m:
            m[cf] = fn
    return m


def _row_get(row, col_map, *names):
    """First matching column (any casing) wins."""
    for name in names:
        key = col_map.get(name)
        if key is None and name:
            key = col_map.get(name.casefold())
        if key is not None:
            return row.get(key)
    return None


def _has_required_headers(col_map, headers):
    for h in headers:
        if h in col_map or h.casefold() in col_map:
            continue
        return False
    return True


def _normalize_breed_group_size(group_raw, size_raw):
    """
    Map CSV group/size strings to model values. Invalid group → (None, None, error).
    Empty or invalid size → None (matches import_dogdb_csv).
    """
    valid_g = _valid_breed_groups()
    valid_s = _valid_breed_sizes()
    group = (group_raw or "").strip()
    size = (size_raw or "").strip()
    mapped_g = _BREED_GROUP_MAP.get(group, group)
    if mapped_g not in valid_g:
        return (
            None,
            None,
            f'Invalid group "{group_raw}". Valid: {", ".join(sorted(valid_g))}',
        )
    if not size:
        return mapped_g, None, None
    mapped_s = _BREED_SIZE_MAP.get(size, size)
    if mapped_s not in valid_s:
        return mapped_g, None, None
    return mapped_g, mapped_s, None


# DogDB.csv column names → model fields (ratings parsed with _parse_breed_csv_rating)
_DOGDB_RATING_COLUMNS = {
    "Friendliness": "friendliness",
    "Family Friendly": "family_friendly",
    "Child Friendly": "child_friendly",
    "Pet Friendly": "pet_friendly",
    "Stranger Friendly": "stranger_friendly",
    "Easy to Groom": "easy_to_groom",
    "Energy Levels": "energy_levels",
    "Health": "health",
    "Shedding Amout": "shedding_amount",
    "Barks / Howls": "barks_howls",
    "Easy to Train": "easy_to_train",
    "Guard Dog": "guard_dog",
    "Playfulness": "playfulness",
    "Apartment Dog": "apartment_dog",
    "Can be Alone": "can_be_alone",
    "Good for Busy Owners": "good_for_busy_owners",
    "Good for New Owners": "good_for_new_owners",
}

_DOGDB_TEXT_COLUMNS = {
    "Lifespan": "lifespan",
    "Height": "height",
    "Weight": "weight",
    "Health Concerns": "health_concerns",
    "Short Description": "short_description",
    "Long Description": "long_description",
}


def _breed_row_from_dogdb(row, col_map):
    breed_name = (_row_get(row, col_map, "Breed") or "").strip()
    group_raw = _row_get(row, col_map, "Group") or ""
    size_raw = _row_get(row, col_map, "Size") or ""
    mapped_g, mapped_s, err = _normalize_breed_group_size(group_raw, size_raw)
    if err:
        return None, err
    data = {
        "breed": breed_name,
        "group": mapped_g,
        "size": mapped_s,
    }
    for csv_col, model_field in _DOGDB_TEXT_COLUMNS.items():
        v = (_row_get(row, col_map, csv_col) or "").strip()
        data[model_field] = v or None
    for csv_col, model_field in _DOGDB_RATING_COLUMNS.items():
        data[model_field] = _parse_breed_csv_rating(
            _row_get(row, col_map, csv_col) or ""
        )
    return data, None


# Optional columns when using simple lowercase headers (same semantics as DogDB extras)
_SIMPLE_EXTRA_RATING = {
    "Friendliness": "friendliness",
    "Family Friendly": "family_friendly",
    "Child Friendly": "child_friendly",
    "Pet Friendly": "pet_friendly",
    "Stranger Friendly": "stranger_friendly",
    "Easy to Groom": "easy_to_groom",
    "Energy Levels": "energy_levels",
    "Health": "health",
    "Shedding Amout": "shedding_amount",
    "Barks / Howls": "barks_howls",
    "Easy to Train": "easy_to_train",
    "Watch dog": "guard_dog",
    "Guard Dog": "guard_dog",
    "Playfulness": "playfulness",
    "Apartment Dog": "apartment_dog",
    "Can be Alone": "can_be_alone",
    "Good for Busy Owners": "good_for_busy_owners",
    "Good for New Owners": "good_for_new_owners",
}

_SIMPLE_EXTRA_TEXT = {
    "Lifespan": "lifespan",
    "Height": "height",
    "Weight": "weight",
    "Health Concerns": "health_concerns",
    "Short Description": "short_description",
    "Long Description": "long_description",
}


def _merge_simple_optional_columns(row, breed_data, col_map):
    """Apply optional Title Case columns if present (shared with DogDB-style files)."""
    for csv_col, model_field in _SIMPLE_EXTRA_TEXT.items():
        v = _row_get(row, col_map, csv_col)
        if v:
            breed_data[model_field] = str(v).strip() or None
    for csv_col, model_field in _SIMPLE_EXTRA_RATING.items():
        v = _row_get(row, col_map, csv_col)
        if v:
            breed_data[model_field] = _parse_breed_csv_rating(v)
    return breed_data


def _breed_bulk_update_field_names():
    """Scalar columns set from CSV imports (not id, breed key, or image uploads)."""
    skip = {"id", "breed", "portrait_image", "landscape_image"}
    return [
        f.name
        for f in Breed._meta.concrete_fields
        if f.name not in skip
    ]


def _apply_breed_import_bulk(valid_rows, update_existing):
    """
    Persist parsed rows with minimal queries (avoids per-row HTTP timeouts / 502).

    valid_rows: list of (row_number, breed_name, defaults) — defaults excludes breed.
    """
    out = {"created": 0, "updated": 0, "errors": 0, "error_details": []}
    if not valid_rows:
        return out

    bulk_fields = _breed_bulk_update_field_names()

    with transaction.atomic():
        if update_existing:
            final = {}
            for row_number, breed_name, defaults in valid_rows:
                final[breed_name] = (row_number, defaults)

            names = list(final.keys())
            existing = {
                b.breed: b
                for b in Breed.objects.filter(breed__in=names).only(
                    "id", "breed", *bulk_fields
                )
            }
            to_create = []
            to_update = []
            for breed_name, (_, defaults) in final.items():
                if breed_name in existing:
                    obj = existing[breed_name]
                    for key, val in defaults.items():
                        setattr(obj, key, val)
                    to_update.append(obj)
                else:
                    to_create.append(Breed(breed=breed_name, **defaults))

            if to_create:
                Breed.objects.bulk_create(to_create, batch_size=200)
            if to_update:
                Breed.objects.bulk_update(to_update, bulk_fields, batch_size=200)

            out["created"] = len(to_create)
            out["updated"] = len(to_update)
        else:
            existing_db = set(Breed.objects.values_list("breed", flat=True))
            seen_file = set()
            to_create = []
            for row_number, breed_name, defaults in valid_rows:
                if breed_name in seen_file:
                    out["errors"] += 1
                    out["error_details"].append(
                        {
                            "row": row_number,
                            "breed": breed_name,
                            "error": "Duplicate breed row in CSV.",
                        }
                    )
                    continue
                seen_file.add(breed_name)
                if breed_name in existing_db:
                    out["errors"] += 1
                    out["error_details"].append(
                        {
                            "row": row_number,
                            "breed": breed_name,
                            "error": (
                                "Breed already exists. Use update=true to update."
                            ),
                        }
                    )
                    continue
                to_create.append(Breed(breed=breed_name, **defaults))
                existing_db.add(breed_name)

            if to_create:
                Breed.objects.bulk_create(to_create, batch_size=200)
            out["created"] = len(to_create)

    return out


def _clamp_breed_defaults_chars(defaults):
    """Trim CharField strings to model max_length before bulk_create / bulk_update."""
    out = dict(defaults)
    for name, val in list(out.items()):
        if val is None or not isinstance(val, str):
            continue
        try:
            field = Breed._meta.get_field(name)
        except Exception:
            continue
        max_len = getattr(field, "max_length", None)
        if max_len and len(val) > max_len:
            out[name] = val[:max_len]
    return out


def _breed_import_database_error_payload(exc):
    msg = str(exc).lower()
    payload = {"error": "Database error during import", "detail": str(exc)}
    if "too long" in msg or "character varying" in msg:
        payload["error"] = "Database columns are too short for this CSV"
        payload["fix"] = (
            "Run database migrations (e.g. `python manage.py migrate`). "
            "Breeds migrations 0003+ widen lifespan, height, and weight; "
            "0005 widens them further. On Render, redeploy so the build runs migrate."
        )
    return payload


def _finalize_breed_import_http_status(results):
    """Attach message and return DRF status for import result dict."""
    if results["errors"] > 0 and results["created"] == 0 and results["updated"] == 0:
        results["message"] = "Import failed with errors"
        return status.HTTP_400_BAD_REQUEST
    if results["errors"] > 0:
        results["message"] = "Import completed with some errors"
        return status.HTTP_207_MULTI_STATUS
    results["message"] = "Import completed successfully"
    return status.HTTP_200_OK


def _import_breeds_from_csv_text(csv_content, update_existing, clear_existing):
    """
    Run breed CSV import from decoded text. Returns results dict (no message / HTTP status).
    """
    if csv_content.startswith("\ufeff"):
        csv_content = csv_content[1:]
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    fieldnames = csv_reader.fieldnames

    if not fieldnames:
        raise ValueError("CSV has no header row")

    col_map = _csv_column_map(fieldnames)
    dogdb_ok = _has_required_headers(col_map, ("Breed", "Group", "Size"))
    simple_ok = _has_required_headers(col_map, ("breed", "group", "size"))

    if dogdb_ok:
        csv_format = "dogdb"
    elif simple_ok:
        csv_format = "simple"
    else:
        raise ValueError(
            "Need either DogDB headers (Breed, Group, Size) or "
            "simple headers (breed, group, size)."
        )

    if clear_existing:
        Breed.objects.all().delete()

    results = {
        "csv_format": csv_format,
        "created": 0,
        "updated": 0,
        "errors": 0,
        "skipped": 0,
        "error_details": [],
    }

    valid_rows = []

    for row_number, row in enumerate(csv_reader, start=2):
        try:
            if csv_format == "dogdb":
                breed_data, err = _breed_row_from_dogdb(row, col_map)
                if err:
                    results["errors"] += 1
                    results["error_details"].append(
                        {
                            "row": row_number,
                            "breed": (
                                _row_get(row, col_map, "Breed") or ""
                            ).strip(),
                            "error": err,
                        }
                    )
                    continue
                breed_name = breed_data["breed"]
                if not breed_name:
                    results["skipped"] += 1
                    continue
                defaults = {k: v for k, v in breed_data.items() if k != "breed"}
            else:
                breed_name = (_row_get(row, col_map, "breed") or "").strip()
                if not breed_name:
                    results["skipped"] += 1
                    continue
                mapped_g, mapped_s, err = _normalize_breed_group_size(
                    _row_get(row, col_map, "group") or "",
                    _row_get(row, col_map, "size") or "",
                )
                if err:
                    results["errors"] += 1
                    results["error_details"].append(
                        {
                            "row": row_number,
                            "breed": breed_name,
                            "error": err,
                        }
                    )
                    continue
                defaults = {"group": mapped_g, "size": mapped_s}
                defaults = _merge_simple_optional_columns(row, defaults, col_map)

            valid_rows.append(
                (
                    row_number,
                    breed_name,
                    _clamp_breed_defaults_chars(defaults),
                )
            )

        except Exception as e:
            results["errors"] += 1
            results["error_details"].append(
                {
                    "row": row_number,
                    "breed": (
                        _row_get(row, col_map, "Breed", "breed") or ""
                    ).strip(),
                    "error": str(e),
                }
            )

    bulk_out = _apply_breed_import_bulk(valid_rows, update_existing)
    results["created"] += bulk_out["created"]
    results["updated"] += bulk_out["updated"]
    results["errors"] += bulk_out["errors"]
    results["error_details"].extend(bulk_out["error_details"])
    results["total_breeds_in_database"] = Breed.objects.count()
    return results


def _assert_breed_csv_fetch_url_allowed(url: str) -> None:
    prefixes = django_settings.BREED_IMPORT_URL_PREFIXES
    if not prefixes:
        raise ValueError(
            "BREED_IMPORT_URL_PREFIXES is not set on the server "
            "(comma-separated allowed URL prefixes)."
        )
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Only https URLs are allowed")
    host = parsed.hostname
    if not host:
        raise ValueError("Invalid URL")
    normalized = url.split("?", 1)[0].rstrip("/")
    if not any(
        normalized.startswith(p + "/") or normalized == p for p in prefixes
    ):
        raise ValueError("URL is not under an allowed prefix")

    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError(f"Could not resolve host: {exc}") from exc
    for info in infos:
        ip_str = info[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
        ):
            raise ValueError("Host resolves to a disallowed address")


def _fetch_breed_csv_bytes(url: str) -> bytes:
    _assert_breed_csv_fetch_url_allowed(url)
    max_b = django_settings.BREED_IMPORT_URL_MAX_BYTES
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "NeoProject-breed-import/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            chunks = []
            total = 0
            while True:
                block = resp.read(65536)
                if not block:
                    break
                total += len(block)
                if total > max_b:
                    raise ValueError("CSV exceeds BREED_IMPORT_URL_MAX_BYTES")
                chunks.append(block)
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Download failed: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Download failed: {exc.reason}") from exc
    return b"".join(chunks)


class BreedViewSet(ModelViewSet):
    queryset = Breed.objects.all()
    serializer_class = BreedSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post']  # Allow GET and POST requests

    # Override list method to provide better response
    def list(self, request, *args, **kwargs):
        """List all breeds with optional filtering"""
        queryset = self.get_queryset()
        
        # Add filtering options
        group = request.query_params.get('group', None)
        if group:
            queryset = queryset.filter(group=group)
        
        size = request.query_params.get('size', None)
        if size:
            queryset = queryset.filter(size=size)
        
        # Add search functionality
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(breed__icontains=search)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # Endpoint to get distinct breed groups
    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='groups')
    def list_groups(self, request):
        groups = Breed.objects.values_list('group', flat=True).distinct().order_by('group')
        return Response(groups, status=status.HTTP_200_OK)

    # Endpoint to get breeds within a specific group
    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='groups/(?P<group>[^/.]+)')
    def list_breeds_in_group(self, request, group=None):
        breeds = Breed.objects.filter(group=group)
        if not breeds.exists():
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(breeds, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Endpoint to get details for a specific breed
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='detail')
    def breed_detail(self, request):
        breed_name = request.data.get('breed')
        
        if not breed_name:
            return Response({'error': 'No breed provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            single_breed = Breed.objects.get(breed=breed_name)
        except Breed.DoesNotExist:
            return Response({'error': 'Breed not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(single_breed)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Endpoint to upload CSV file and import breeds
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='import-csv')
    def import_csv(self, request):
        """
        Import breeds from an uploaded CSV file (multipart form).

        Form fields:
        - csv_file: CSV file (required)
        - update: optional, "true" / "false" (default false)
        - clear: optional, "true" / "false" — delete all breeds before import

        Supported CSV layouts:
        - DogDB: columns Breed, Group, Size (plus optional DogDB trait columns)
        - Simple: columns breed, group, size (plus optional Title Case extras)
        """
        try:
            if 'csv_file' not in request.FILES:
                return Response({
                    'error': 'No CSV file provided',
                    'detail': 'Please upload a CSV file using the csv_file field'
                }, status=status.HTTP_400_BAD_REQUEST)

            csv_file = request.FILES['csv_file']

            if not csv_file.name.lower().endswith('.csv'):
                return Response({
                    'error': 'Invalid file type',
                    'detail': 'Please upload a CSV file'
                }, status=status.HTTP_400_BAD_REQUEST)

            update_existing = request.data.get('update', 'false').lower() == 'true'
            clear_existing = request.data.get('clear', 'false').lower() == 'true'

            try:
                csv_content = csv_file.read().decode('utf-8')
                try:
                    results = _import_breeds_from_csv_text(
                        csv_content, update_existing, clear_existing
                    )
                except ValueError as exc:
                    return Response(
                        {
                            'error': 'Invalid CSV format',
                            'detail': str(exc),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                except DatabaseError as exc:
                    return Response(
                        _breed_import_database_error_payload(exc),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                response_status = _finalize_breed_import_http_status(results)
                return Response(results, status=response_status)

            except UnicodeDecodeError:
                return Response({
                    'error': 'File encoding error',
                    'detail': 'Please ensure the CSV file is UTF-8 encoded'
                }, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                return Response({
                    'error': 'CSV processing error',
                    'detail': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': 'Import failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[AllowAny],
        url_path='import-csv-url',
    )
    def import_csv_url(self, request):
        """
        Import breeds by URL (tiny JSON request; server downloads CSV). For hosts where
        multipart uploads hit timeouts — no Render Shell needed.

        Headers:
            X-Breed-Import-Token: must match env BREED_IMPORT_URL_TOKEN

        JSON body:
            csv_url (required): https URL whose prefix is allowed by BREED_IMPORT_URL_PREFIXES
            update (optional): true/false
            clear (optional): true/false
        """
        token_cfg = django_settings.BREED_IMPORT_URL_TOKEN
        if not token_cfg:
            return Response(
                {
                    'error': 'URL import disabled',
                    'detail': (
                        'Set BREED_IMPORT_URL_TOKEN and BREED_IMPORT_URL_PREFIXES '
                        'on the server (Render → Environment).'
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.headers.get('X-Breed-Import-Token') != token_cfg:
            return Response(
                {
                    'error': 'Unauthorized',
                    'detail': 'Send header X-Breed-Import-Token matching the server secret.',
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        csv_url = request.data.get('csv_url')
        if not csv_url or not isinstance(csv_url, str):
            return Response(
                {
                    'error': 'csv_url required',
                    'detail': 'JSON body: {"csv_url": "https://...", "update": true}',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        update_existing = (
            str(request.data.get('update', 'false')).lower() in ('true', '1', 'yes')
        )
        clear_existing = (
            str(request.data.get('clear', 'false')).lower() in ('true', '1', 'yes')
        )

        try:
            raw = _fetch_breed_csv_bytes(csv_url.strip())
            csv_content = raw.decode('utf-8')
        except ValueError as exc:
            return Response(
                {'error': 'Could not download CSV', 'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except UnicodeDecodeError:
            return Response(
                {'error': 'File encoding error', 'detail': 'CSV must be UTF-8'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            results = _import_breeds_from_csv_text(
                csv_content, update_existing, clear_existing
            )
        except ValueError as exc:
            return Response(
                {'error': 'Invalid CSV format', 'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DatabaseError as exc:
            return Response(
                _breed_import_database_error_payload(exc),
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_status = _finalize_breed_import_http_status(results)
        results['source'] = 'url'
        return Response(results, status=response_status)

    # Endpoint to match breeds based on preferences
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='match')
    def match_breeds(self, request):
        """
        Match breeds based on user preferences.
        
        Accepts preferences for various breed attributes and returns the top 5
        breeds that best match the criteria, along with match percentages.
        
        Example request body:
        {
            "size": "M",
            "pet_friendly": 8,
            "apartment_dog": 7,
            "easy_to_groom": 6,
            "family_friendly": 9,
            "energy_levels": 5
        }
        """
        # Validate request data
        request_serializer = BreedMatchRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response({
                'error': 'Invalid request data',
                'details': request_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        preferences = request_serializer.validated_data
        
        # Check if at least one preference is provided
        if not any(preferences.values()):
            return Response({
                'error': 'At least one preference must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all breeds
        breeds = Breed.objects.all()
        
        # Calculate match scores for each breed
        breed_matches = []
        
        for breed in breeds:
            match_scores = []
            total_weight = 0
            
            # Size matching (exact match)
            if preferences.get('size') is not None:
                if breed.size == preferences['size']:
                    match_scores.append(100.0)
                    total_weight += 1
                elif breed.size is not None:
                    match_scores.append(0.0)
                    total_weight += 1
            
            # Numeric field matching (1-10 scale)
            numeric_fields = [
                'pet_friendly', 'apartment_dog', 'easy_to_groom', 'family_friendly',
                'child_friendly', 'energy_levels', 'easy_to_train', 'can_be_alone',
                'good_for_busy_owners', 'good_for_new_owners', 'shedding_amount',
                'barks_howls', 'playfulness', 'friendliness', 'stranger_friendly',
                'guard_dog', 'health'
            ]
            
            for field in numeric_fields:
                user_pref = preferences.get(field)
                if user_pref is not None:
                    breed_value = getattr(breed, field, None)
                    if breed_value is not None:
                        # Calculate match percentage based on how close values are
                        # Perfect match (same value) = 100%
                        # Difference of 1 = 90%, difference of 2 = 80%, etc.
                        # Minimum match = 0% for difference >= 10
                        difference = abs(user_pref - breed_value)
                        match_percentage = max(0, 100 - (difference * 10))
                        match_scores.append(match_percentage)
                        total_weight += 1
            
            # Calculate overall match rate
            if total_weight > 0 and match_scores:
                overall_match = sum(match_scores) / total_weight
                breed_matches.append({
                    'breed': breed,
                    'match_rate': round(overall_match, 2)
                })
        
        # Sort by match rate (descending) and filter out 0% matches
        breed_matches.sort(key=lambda x: x['match_rate'], reverse=True)
        # Only include breeds with match rate greater than 0%
        non_zero_matches = [match for match in breed_matches if match['match_rate'] > 0]
        # Get top 5 (or fewer if less than 5 have > 0% match)
        top_5_matches = non_zero_matches[:5]
        
        # Serialize results
        results = []
        for match in top_5_matches:
            breed_serializer = BreedSerializer(match['breed'])
            results.append({
                'breed': breed_serializer.data,
                'match_rate': match['match_rate']
            })
        
        return Response({
            'matches': results,
            'total_breeds_compared': len(breed_matches),
            'preferences_used': {k: v for k, v in preferences.items() if v is not None}
        }, status=status.HTTP_200_OK)
