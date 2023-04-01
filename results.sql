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
-- Data for Name: beat_the_odds_result; Type: TABLE DATA; Schema: public; Owner: jfagan
--

COPY public.beat_the_odds_result (id, wins, losses, participant_id, points, contest_id, ties) FROM stdin;
5	3	2	5	-122	1	0
6	3	2	6	995	1	0
7	4	1	3	252	1	0
8	3	2	1	578	1	0
\.


--
-- Name: beat_the_odds_stat_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jfagan
--

SELECT pg_catalog.setval('public.beat_the_odds_stat_id_seq', 12, true);


--
-- PostgreSQL database dump complete
--

