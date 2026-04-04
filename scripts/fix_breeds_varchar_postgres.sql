-- Emergency fix if Django migrations cannot run against your Render Postgres.
-- Run in psql, Render Postgres "Shell", or any SQL client connected to the same DB as the app.

ALTER TABLE public.breeds_breed
  ALTER COLUMN lifespan TYPE varchar(48) USING lifespan::varchar(48),
  ALTER COLUMN height TYPE varchar(48) USING height::varchar(48),
  ALTER COLUMN weight TYPE varchar(48) USING weight::varchar(48);

ALTER TABLE public.breeds_breed
  ALTER COLUMN breed TYPE varchar(64) USING breed::varchar(64);

-- size is varchar(5) in the model; widening to 48 is safe if you still see length errors:
-- ALTER TABLE public.breeds_breed
--   ALTER COLUMN size TYPE varchar(48) USING size::varchar(48);
