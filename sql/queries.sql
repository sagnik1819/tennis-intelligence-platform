-- ==============================================================================
-- TENNIS INTELLIGENCE PLATFORM (TIP) - 20 CORE ANALYTICAL SQL QUERIES
-- Derived directly from the curriculum and project capstone requirements
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- PART 1: COMPETITION & CATEGORY ANALYTICS (Queries 1 - 7)
-- ------------------------------------------------------------------------------

-- Query 1: List all competitions along with their category name
SELECT 
    c.competition_id,
    c.competition_name,
    c.type,
    c.gender,
    cat.category_name
FROM competitions c
JOIN categories cat ON c.category_id = cat.category_id
ORDER BY cat.category_name, c.competition_name;

-- Query 2: Count the number of competitions in each category
SELECT 
    cat.category_name,
    COUNT(c.competition_id) AS competition_count
FROM categories cat
LEFT JOIN competitions c ON cat.category_id = c.category_id
GROUP BY cat.category_name
ORDER BY competition_count DESC;

-- Query 3: Find all competitions of type 'doubles'
SELECT 
    competition_id,
    competition_name,
    gender,
    type
FROM competitions
WHERE LOWER(type) = 'doubles'
ORDER BY competition_name;

-- Query 4: Get competitions that belong to a specific category (e.g., 'ITF Men')
SELECT 
    c.competition_id,
    c.competition_name,
    c.type,
    cat.category_name
FROM competitions c
JOIN categories cat ON c.category_id = cat.category_id
WHERE cat.category_name = 'ITF Men';

-- Query 5: Identify parent competitions and their sub-competitions
SELECT 
    p.competition_name AS parent_competition,
    s.competition_name AS sub_competition
FROM competitions s
JOIN competitions p ON s.parent_id = p.competition_id
ORDER BY parent_competition, sub_competition;

-- Query 6: Analyze the distribution of competition types by category
SELECT 
    cat.category_name,
    c.type,
    COUNT(*) AS total_events
FROM competitions c
JOIN categories cat ON c.category_id = cat.category_id
GROUP BY cat.category_name, c.type
ORDER BY cat.category_name, total_events DESC;

-- Query 7: List all competitions with no parent (top-level competitions)
SELECT 
    competition_id,
    competition_name,
    type,
    gender
FROM competitions
WHERE parent_id IS NULL
ORDER BY competition_name;


-- ------------------------------------------------------------------------------
-- PART 2: COMPLEXES & VENUES ANALYTICS (Queries 8 - 14)
-- ------------------------------------------------------------------------------

-- Query 8: List all venues along with their associated complex name
SELECT 
    v.venue_id,
    v.venue_name,
    v.city_name,
    v.country_name,
    cx.complex_name
FROM venues v
JOIN complexes cx ON v.complex_id = cx.complex_id
ORDER BY cx.complex_name, v.venue_name;

-- Query 9: Count the number of venues in each complex
SELECT 
    cx.complex_name,
    COUNT(v.venue_id) AS total_venues
FROM complexes cx
LEFT JOIN venues v ON cx.complex_id = v.complex_id
GROUP BY cx.complex_name
ORDER BY total_venues DESC;

-- Query 10: Get details of venues in a specific country (e.g., 'Chile')
SELECT 
    venue_id,
    venue_name,
    city_name,
    country_name,
    timezone
FROM venues
WHERE country_name = 'Chile'
ORDER BY city_name, venue_name;

-- Query 11: Identify all venues and their timezones
SELECT 
    venue_name,
    city_name,
    country_name,
    timezone
FROM venues
ORDER BY timezone, venue_name;

-- Query 12: Find complexes that have more than one venue
SELECT 
    cx.complex_id,
    cx.complex_name,
    COUNT(v.venue_id) AS venue_count
FROM complexes cx
JOIN venues v ON cx.complex_id = v.complex_id
GROUP BY cx.complex_id, cx.complex_name
HAVING COUNT(v.venue_id) > 1
ORDER BY venue_count DESC;

-- Query 13: List venues grouped by country
SELECT 
    country_name,
    COUNT(venue_id) AS total_venues
FROM venues
GROUP BY country_name
ORDER BY total_venues DESC;

-- Query 14: Find all venues for a specific complex (e.g., complex containing 'Nacional')
SELECT 
    v.venue_id,
    v.venue_name,
    v.city_name,
    cx.complex_name
FROM venues v
JOIN complexes cx ON v.complex_id = cx.complex_id
WHERE cx.complex_name LIKE '%Nacional%'
ORDER BY v.venue_name;


-- ------------------------------------------------------------------------------
-- PART 3: COMPETITORS & RANKINGS ANALYTICS (Queries 15 - 20)
-- ------------------------------------------------------------------------------

-- Query 15: Get all competitors with their rank and points
SELECT 
    c.name AS competitor_name,
    c.country,
    c.country_code,
    r.rank,
    r.points,
    r.competitions_played
FROM competitor_rankings r
JOIN competitors c ON r.competitor_id = c.competitor_id
ORDER BY r.rank ASC;

-- Query 16: Find competitors ranked in the top 5
SELECT 
    r.rank,
    c.name AS competitor_name,
    c.country,
    r.points
FROM competitor_rankings r
JOIN competitors c ON r.competitor_id = c.competitor_id
WHERE r.rank <= 5
ORDER BY r.rank ASC;

-- Query 17: List competitors with no rank movement (stable rank)
SELECT 
    r.rank,
    c.name AS competitor_name,
    c.country,
    r.movement
FROM competitor_rankings r
JOIN competitors c ON r.competitor_id = c.competitor_id
WHERE r.movement = 0
ORDER BY r.rank ASC;

-- Query 18: Get the total points of competitors from a specific country (e.g., 'Croatia')
SELECT 
    c.country,
    SUM(r.points) AS total_country_points,
    COUNT(c.competitor_id) AS total_ranked_players
FROM competitor_rankings r
JOIN competitors c ON r.competitor_id = c.competitor_id
WHERE c.country = 'Croatia'
GROUP BY c.country;

-- Query 19: Count the number of competitors per country
SELECT 
    country,
    country_code,
    COUNT(competitor_id) AS player_count
FROM competitors
GROUP BY country, country_code
ORDER BY player_count DESC, country ASC;

-- Query 20: Find competitors with the highest points in the current week
SELECT 
    c.name AS competitor_name,
    c.country,
    r.rank,
    r.points
FROM competitor_rankings r
JOIN competitors c ON r.competitor_id = c.competitor_id
WHERE r.points = (SELECT MAX(points) FROM competitor_rankings);
