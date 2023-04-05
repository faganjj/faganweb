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
-- Data for Name: beat_the_odds_contest; Type: TABLE DATA; Schema: public; Owner: jfagan
--

COPY public.beat_the_odds_contest (id, league, season, period, num_picks, num_games, winner, status, test_contest) FROM stdin;
1	NFL	2020	Week 15	5	16		Complete	t
\.


--
-- Name: beat_the_odds_contest_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jfagan
--

SELECT pg_catalog.setval('public.beat_the_odds_contest_id_seq', 4, true);


--
-- PostgreSQL database dump complete
--

