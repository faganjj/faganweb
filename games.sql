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
-- Data for Name: beat_the_odds_game; Type: TABLE DATA; Schema: public; Owner: jfagan
--

COPY public.beat_the_odds_game (id, game_date, game_time, team_away, team_home, odds_away, odds_home, score_away, score_home, outcome_away, outcome_home, contest_id) FROM stdin;
1	2020-12-17	20:20:00	LAC	LV	150	-170	30	27	W	L	1
2	2020-12-19	20:15:00	CAR	GB	340	-420	16	24	L	W	1
3	2020-12-19	16:30:00	BUF	DEN	-260	220	48	19	W	L	1
4	2020-12-20	13:00:00	HOU	IND	270	-330	20	27	L	W	1
5	2020-12-20	13:00:00	DET	TEN	500	-700	25	46	L	W	1
6	2020-12-20	16:05:00	NYJ	LAR	1000	-2000	23	20	W	L	1
7	2020-12-20	13:00:00	TB	ATL	-260	220	31	27	W	L	1
8	2020-12-20	13:00:00	NE	MIA	110	-130	12	22	L	W	1
9	2020-12-20	13:00:00	SEA	WAS	-250	210	20	15	W	L	1
10	2020-12-20	13:00:00	CHI	MIN	155	-175	33	27	W	L	1
11	2020-12-20	13:00:00	JAC	BAL	650	-1000	14	40	L	W	1
12	2020-12-20	20:20:00	CLE	NYG	-210	180	20	8	W	L	1
13	2020-12-20	16:05:00	PHI	ARI	240	-280	26	33	L	W	1
14	2020-12-20	16:25:00	KC	NO	-170	150	33	29	W	L	1
15	2020-12-20	13:00:00	SF	DAL	-160	140	33	41	L	W	1
16	2020-12-21	20:15:00	PIT	CIN	-900	600	17	27	L	W	1
\.


--
-- Name: beat_the_odds_game_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jfagan
--

SELECT pg_catalog.setval('public.beat_the_odds_game_id_seq', 17, true);


--
-- PostgreSQL database dump complete
--

