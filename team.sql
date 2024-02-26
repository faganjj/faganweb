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
63	NHL	BOS	Boston Bruins
64	NHL	BUF	Buffalo Sabres
65	NHL	CAR	Carolina Hurricanes
66	NHL	CBJ	Columbus Blue Jackets
67	NHL	DET	Detroit Red Wings
68	NHL	FLA	Florida Panthers
70	NHL	NJ	New Jersey Devils
71	NHL	NYI	New York Islanders
72	NHL	NYR	New York Rangers
73	NHL	OTT	Ottawa Senators
74	NHL	PHI	Philadelphia Flyers
75	NHL	PIT	Pittsburgh Penguins
76	NHL	TB	Tampa Bay Lightning
77	NHL	TOR	Toronto Maple Leafs
78	NHL	WSH	Washington Capitals
79	NHL	ANA	Anaheim Ducks
80	NHL	ARI	Arizona Coyotes
81	NHL	CGY	Calgary Flames
82	NHL	CHI	Chicago Blackhawks
83	NHL	COL	Colorado Avalanche
84	NHL	DAL	Dallas Stars
85	NHL	EDM	Edmonton Oilers
86	NHL	LA	Los Angeles Kings
87	NHL	MIN	Minnesota Wild
88	NHL	NSH	Nashville Predators
90	NHL	SJ	San Jose Sharks
91	NHL	STL	St Louis Blues
92	NHL	VAN	Vancouver Canucks
93	NHL	VGK	Vegas Golden Knights
94	NHL	WPG	Winnipeg Jets
69	NHL	MTL	Montréal Canadiens
89	NHL	SEA	Seattle Kraken
\.


--
-- Name: beat_the_odds_team_id_seq; Type: SEQUENCE SET; Schema: public; Owner: jfagan
--

SELECT pg_catalog.setval('public.beat_the_odds_team_id_seq', 94, true);


--
-- PostgreSQL database dump complete
--

