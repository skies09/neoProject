-- Emergency fix if Django migrations cannot run against your Render Postgres.
-- Run in psql, Render Postgres "Shell", or any SQL client connected to the same DB as the app.

-- TEXT removes varchar length limits entirely (matches breeds.0008).
ALTER TABLE public.breeds_breed
  ALTER COLUMN lifespan TYPE text USING lifespan::text,
  ALTER COLUMN height TYPE text USING height::text,
  ALTER COLUMN weight TYPE text USING weight::text;

ALTER TABLE public.breeds_breed
  ALTER COLUMN breed TYPE varchar(64) USING breed::varchar(64);

-- size is varchar(5) in the model; widening to 48 is safe if you still see length errors:
-- ALTER TABLE public.breeds_breed
--   ALTER COLUMN size TYPE varchar(48) USING size::varchar(48);
