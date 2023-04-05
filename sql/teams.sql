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
-- Data for Name: beat_the_odds_team; Type: TABLE DATA; Schema: public; Owner: jfagan
--

COPY public.beat_the_odds_team (id, league, abbrev, name) FROM stdin;
1	NFL	LAC	Los Angeles Chargers
2	NFL	LV	Las Vegas Raiders
3	NFL	CAR	Carolina Panthers
4	NFL	GB	Green Bay Packers
5	NFL	BUF	Buffalo Bills
6	NFL	DEN	Denver Broncos
7	NFL	HOU	Houston Texans
8	NFL	IND	Indianapolis Colts
9	NFL	DET	Detroit Lions
10	NFL	TEN	Tennessee Titans
11	NFL	NYJ	New York Jets
12	NFL	LAR	Los Angeles Rams
13	NFL	TB	Tampa Bay Buccaneers
14	NFL	ATL	Atlanta Falcons
15	NFL	NE	New England Patriots
16	NFL	MIA	Miami Dolphins
17	NFL	SEA	Seattle Seahawks
18	NFL	WAS	Washington Commanders
19	NFL	CHI	Chicago Bears
20	NFL	MIN	Minnesota Vikings
21	NFL	JAC	Jacksonville Jaguars
22	NFL	BAL	Baltimore Ravens
23	NFL	CLE	Cleveland Browns
24	NFL	NYG	New York Giants
25	NFL	PHI	Philadelphia Eagles
26	NFL	ARI	Arizona Cardinals
27	NFL	KC	Kansas City Chiefs
28	NFL	NO	New Orleans Saints
29	NFL	SF	San Francisco 49ers
30	NFL	DAL	Dallas Cowboys
31	NFL	PIT	Pittsburgh Steelers
32	NFL	CIN	Cincinnati Bengals
\.


--
-- Name: beat_the_odds_team_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jfagan
--

SELECT pg_catalog.setval('public.beat_the_odds_team_id_seq', 32, true);


--
-- PostgreSQL database dump complete
--

