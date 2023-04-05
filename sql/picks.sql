--
-- PostgreSQL database dump
--

-- Dumped from database version 13.1
-- Dumped by pg_dump version 13.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: beat_the_odds_pick; Type: TABLE DATA; Schema: public; Owner: jfagan
--

COPY public.beat_the_odds_pick (id, abbrev, contest_id, participant_id) FROM stdin;
11	GB	1	5
12	TEN	1	5
13	SEA	1	5
14	PHI	1	5
15	PIT	1	5
16	LAC	1	3
17	TEN	1	3
18	CLE	1	3
19	PHI	1	3
20	DAL	1	3
26	LV	1	6
27	NYJ	1	6
28	ATL	1	6
29	SEA	1	6
30	CHI	1	6
41	BUF	1	1
42	NE	1	1
43	NO	1	1
44	DAL	1	1
45	CIN	1	1
\.


--
-- Name: beat_the_odds_pick_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jfagan
--

SELECT pg_catalog.setval('public.beat_the_odds_pick_id_seq', 45, true);


--
-- PostgreSQL database dump complete
--

