drop table if exists queries_tags;
drop table if exists queries_versions;
drop table if exists queries;
drop table if exists accounts;
drop table if exists versions;
drop table if exists tags;

create table tags (
  id serial primary key,
  tag text not null
);

create table versions (
  version_num integer primary key,
  version text not null
);

insert into versions values (80300, '8.3'),(80400, '8.4'),(90000, '9.0'),
  (90100, '9.1'),(90200, '9.2'),(90300, '9.3'),(90400, '9.4');

create table accounts (
  id serial primary key,
  account text unique not null,
  fullname text not null,
  password text not null,
  email text not null,
  is_admin boolean default false not null
);

-- admin/admin
insert into accounts values (1, 'admin', 'Admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'root@example.com');

create table queries (
  id serial primary key,
  query text not null,
  title text not null,
  description text,
  account_id integer not null references accounts (id)
);

create index queries_account_id_key on queries (account_id);

-- Link queries to PostgreSQL versions where the query works
create table queries_versions (
  query_id integer not null references queries (id),
  version_num integer not null references versions (version_num),
  primary key (query_id, version_num)
);

create index queries_versions_version_num_key on queries_versions (version_num);


create table queries_tags (
  query_id integer not null references queries (id),
  tag_id integer not null references tags (id),
  primary key (tag_id, query_id)
);

create index queries_tags_query_id_key on queries_tags (query_id);


