-- The whole database for the wall. Paste this into the Neon SQL editor once.
--
-- No migration tool, deliberately. One table, of names, that will not change
-- shape. Alembic exists in this project for the app's own schema, which is a
-- different database on a different machine.
--
-- There is no email column and no raw IP. Nothing here is worth leaking.

create table if not exists signups (
  id         bigint generated always as identity primary key,
  name       text        not null check (length(name) between 1 and 24),
  country    char(2)     not null,
  gender     text        not null check (gender in ('female','male','neutral')),
  seed       text        not null check (length(seed) <= 64),
  -- sha256(ip + SIGNUP_IP_SALT). Rate limiting works the same on a hash, and
  -- then there is no address in here to lose.
  ip_hash    text        not null,
  -- A uuid the browser keeps in localStorage. Superseded by google_sub below,
  -- and kept only so rows created before sign-in existed still resolve.
  client_id  text,
  created_at timestamptz not null default now()
);

-- Google's `sub` for the account that owns this row: stable, opaque, and not
-- an email address. This is the whole of what signing in adds to the database,
-- which is why there is no adapter and no users/accounts/sessions tables.
alter table signups add column if not exists google_sub text;

-- The board read.
create index if not exists signups_created_at_idx on signups (created_at desc);

-- The rate limit lookup, which runs inside the insert.
create index if not exists signups_ip_hash_created_at_idx on signups (ip_hash, created_at desc);

-- One row per browser. Partial, so the many null client_ids do not collide.
create unique index if not exists signups_client_id_key
  on signups (client_id) where client_id is not null;

-- One row per Google account, for the same reason and in the same shape.
create unique index if not exists signups_google_sub_key
  on signups (google_sub) where google_sub is not null;
