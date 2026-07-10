-- Run this entire file in Supabase SQL Editor (supabase.com → your project → SQL Editor)

create table seen_jobs (
  job_id text primary key,
  company text,
  role text,
  source text,
  url text,
  created_at timestamptz default now()
);

create table jobs (
  id uuid primary key default gen_random_uuid(),
  job_id text unique not null,
  company text not null,
  role text not null,
  location text default '',
  url text default '',
  source text,
  ats text,
  ats_job_id text,
  ats_slug text,
  description text default '',
  created_at timestamptz default now()
);
create index on jobs(created_at desc);
create index on jobs(source);

create table resumes (
  id uuid primary key default gen_random_uuid(),
  name text unique not null,
  content text not null,
  created_at timestamptz default now()
);

create table applications (
  id uuid primary key default gen_random_uuid(),
  company text not null,
  role text not null,
  url text default '',
  source text,
  ats text,
  resume_id uuid references resumes(id) on delete set null,
  status text default 'applied',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index on applications(status);
create index on applications(created_at desc);

create table push_subscriptions (
  endpoint text primary key,
  subscription jsonb not null,
  created_at timestamptz default now()
);
