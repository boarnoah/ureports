drop table if exists agents;
create table agents (
	id text primary key,
	name text not null,
	location text not null,
	online integer,
	description text,
	picture text
);

drop table if exists reports;
create table reports (
	id text primary key,
	time integer not null,
	location text not null,
	agent text references agents(id)
);

drop table if exists images;
create table images (
	id text primary key,
	path text not null,
	confirmed integer not null,
	confidence real,
	type text,
	report text references reports(id)
);