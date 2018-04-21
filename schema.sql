drop table if exists agents;
create table agents (
	id text primary key,
	name text not null,
	location text not null,
	secret text not null,
	online integer,
	description text
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
	location text not null,
	confirmed integer not null,
	report text references reports(id)
);