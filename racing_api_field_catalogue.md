# Racing API — field catalogue (generated)

**Source:** `openapi.json` · **API:** The Racing API v1.4.3  
**Generated:** 2026-06-22 19:18 · **Regenerate:** `python3 gen_racing_api_catalogue.py`

Auto-generated, not hand-maintained — regenerate when the API version bumps. A grep reference: every endpoint and every response data point the API exposes. Curated capability + roles live in `data_sources.md`.

---

## Endpoints (58)

| Method · Path | Summary | Min plan | Rate limit |
|---|---|---|---|
| `GET /v1/australia/meets` | Meets | Free + Australia regional add-on | 5 requests per second |
| `GET /v1/australia/meets/{meet_id}/races` | Races By Meet | Free + Australia regional add-on | 5 requests per second |
| `GET /v1/australia/meets/{meet_id}/races/{race_number}` | Race | Free + Australia regional add-on | 5 requests per second |
| `GET /v1/courses` | Courses | Free | 1 requests per second |
| `GET /v1/courses/regions` | Regions | Free | 1 requests per second |
| `GET /v1/dams/search` | Dam Search | Standard | 5 requests per second |
| `GET /v1/dams/{dam_id}/analysis/classes` | Dam Progeny Class Analysis | Standard | 5 requests per second |
| `GET /v1/dams/{dam_id}/analysis/distances` | Dam Progeny Distance Analysis | Standard | 5 requests per second |
| `GET /v1/dams/{dam_id}/results` | Dam Progeny Results | Pro | 5 requests per second |
| `GET /v1/damsires/search` | Damsire Search | Standard | 5 requests per second |
| `GET /v1/damsires/{damsire_id}/analysis/classes` | Damsire Grandoffspring Class Analysis | Standard | 5 requests per second |
| `GET /v1/damsires/{damsire_id}/analysis/distances` | Damsire Grandoffspring Distance Analysis | Standard | 5 requests per second |
| `GET /v1/damsires/{damsire_id}/results` | Damsire Grandoffspring Results | Pro | 5 requests per second |
| `GET /v1/horses/search` | Horse Search | Standard | 5 requests per second |
| `GET /v1/horses/{horse_id}/analysis/distance-times` | Horse Distance Time Analysis | Basic | 5 requests per second |
| `GET /v1/horses/{horse_id}/pro` | Horse Pro | Pro | 5 requests per second |
| `GET /v1/horses/{horse_id}/results` | Horse Results | Pro | 5 requests per second |
| `GET /v1/horses/{horse_id}/standard` | Horse Standard | Standard | 5 requests per second |
| `GET /v1/jockeys/search` | Jockey Search | Standard | 5 requests per second |
| `GET /v1/jockeys/{jockey_id}/analysis/courses` | Jockey Course Analysis | Standard | 5 requests per second |
| `GET /v1/jockeys/{jockey_id}/analysis/distances` | Jockey Distance Analysis | Standard | 5 requests per second |
| `GET /v1/jockeys/{jockey_id}/analysis/owners` | Jockey Owner Analysis | Standard | 5 requests per second |
| `GET /v1/jockeys/{jockey_id}/analysis/trainers` | Jockey Trainer Analysis | Standard | 5 requests per second |
| `GET /v1/jockeys/{jockey_id}/results` | Jockey Results | Pro | 5 requests per second |
| `GET /v1/north-america/meets` | Meets | Free + North America regional add-on | 5 requests per second |
| `GET /v1/north-america/meets/{meet_id}/entries` | Meet Entries | Free + North America regional add-on | 5 requests per second |
| `GET /v1/north-america/meets/{meet_id}/results` | Meet Results | Free + North America regional add-on | 5 requests per second |
| `GET /v1/odds/{race_id}/{horse_id}` | Odds Runner | Pro | 5 requests per second |
| `GET /v1/owners/search` | Owner Search | Standard | 5 requests per second |
| `GET /v1/owners/{owner_id}/analysis/courses` | Owner Course Analysis | Standard | 5 requests per second |
| `GET /v1/owners/{owner_id}/analysis/distances` | Owner Distance Analysis | Standard | 5 requests per second |
| `GET /v1/owners/{owner_id}/analysis/jockeys` | Owner Jockey Analysis | Standard | 5 requests per second |
| `GET /v1/owners/{owner_id}/analysis/trainers` | Owner Trainer Analysis | Standard | 5 requests per second |
| `GET /v1/owners/{owner_id}/results` | Owner Results | Pro | 5 requests per second |
| `GET /v1/racecards/basic` | Racecards Basic | Basic | 2 requests per second |
| `GET /v1/racecards/big-races` | Racecards Big Races | Standard | 2 requests per second |
| `GET /v1/racecards/free` | Racecards Free | Free | 1 request per second |
| `GET /v1/racecards/pro` | Racecards Pro | Pro | 2 requests per second |
| `GET /v1/racecards/standard` | Racecards Standard | Standard | 2 requests per second |
| `GET /v1/racecards/summaries` | Racecards Summaries | Basic | 5 requests per second |
| `GET /v1/racecards/{horse_id}/results` | Racecard Horse Results | Basic | 5 requests per second |
| `GET /v1/racecards/{race_id}/pro` | Race Pro | Pro | 5 requests per second |
| `GET /v1/racecards/{race_id}/standard` | Race Standard | Standard | 5 requests per second |
| `GET /v1/results` | Results | Standard | 5 requests per second |
| `GET /v1/results/today` | Results Today | Basic | 5 requests per second |
| `GET /v1/results/today/free` | Results Today Free | Free | 1 requests per second |
| `GET /v1/results/{race_id}` | Result | Standard | 5 requests per second |
| `GET /v1/sires/search` | Sire Search | Standard | 5 requests per second |
| `GET /v1/sires/{sire_id}/analysis/classes` | Sire Progeny Class Analysis | Standard | 5 requests per second |
| `GET /v1/sires/{sire_id}/analysis/distances` | Sire Progeny Distance Analysis | Standard | 5 requests per second |
| `GET /v1/sires/{sire_id}/results` | Sire Progeny Results | Pro | 5 requests per second |
| `GET /v1/trainers/search` | Trainer Search | Standard | 5 requests per second |
| `GET /v1/trainers/{trainer_id}/analysis/courses` | Trainer Course Analysis | Standard | 5 requests per second |
| `GET /v1/trainers/{trainer_id}/analysis/distances` | Trainer Distance Analysis | Standard | 5 requests per second |
| `GET /v1/trainers/{trainer_id}/analysis/horse-age` | Trainer Horse Age Analysis | Standard | 5 requests per second |
| `GET /v1/trainers/{trainer_id}/analysis/jockeys` | Trainer Jockey Analysis | Standard | 5 requests per second |
| `GET /v1/trainers/{trainer_id}/analysis/owners` | Trainer Owner Analysis | Standard | 5 requests per second |
| `GET /v1/trainers/{trainer_id}/results` | Trainer Results | Pro | 5 requests per second |

---

## Data schemas — fields (124)

### Change
- `type` — string (nullable)
- `text` — string (nullable)

### CoursesPage
- `courses` — array<app__models__courses__Course> *(req)*
- `total` — integer *(req)*

### Dam
- `id` — string *(req)*
- `name` — string (nullable) *(req)*

### DamClassAnalysis
- `id` — string *(req)*
- `dam` — string *(req)*
- `total_runners` — integer *(req)*
- `classes` — array<app__models__dams__Class> *(req)*
- `query` — array<array<any>> *(req)*

### DamDistanceAnalysis
- `id` — string *(req)*
- `dam` — string *(req)*
- `total_runners` — integer *(req)*
- `distances` — array<app__models__dams__Distance> *(req)*
- `query` — array<array<any>> *(req)*

### Dams
- `search_results` — array<Dam> *(req)*

### Damsire
- `id` — string *(req)*
- `name` — string (nullable) *(req)*

### DamsireClassAnalysis
- `id` — string *(req)*
- `damsire` — string *(req)*
- `total_runners` — integer *(req)*
- `classes` — array<app__models__damsires__Class> *(req)*
- `query` — array<array<any>> *(req)*

### DamsireDistanceAnalysis
- `id` — string *(req)*
- `damsire` — string *(req)*
- `total_runners` — integer *(req)*
- `distances` — array<app__models__damsires__Distance> *(req)*
- `query` — array<array<any>> *(req)*

### Damsires
- `search_results` — array<Damsire> *(req)*

### Distances
- `dist` — string *(req)*
- `dist_y` — string *(req)*
- `dist_m` — string *(req)*
- `dist_f` — string *(req)*
- `times` — array<TimesGoing> *(req)*
- `runs` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### Entries
- `meet_id` — string *(req)*
- `track_id` — string *(req)*
- `track_name` — string *(req)*
- `country` — string *(req)*
- `date` — string *(req)*
- `races` — array<app__models__na_entries__Race> *(req)*
- `weather` — app__models__na_entries__Weather (nullable)

### Fraction
- `fraction_1` — TimeData (nullable)
- `fraction_2` — TimeData (nullable)
- `fraction_3` — TimeData (nullable)
- `fraction_4` — TimeData (nullable)
- `fraction_5` — TimeData (nullable)
- `winning_time` — TimeData (nullable)

### HTTPValidationError
- `detail` — array<ValidationError>

### Horse
- `id` — string *(req)*
- `dam` — string (nullable)
- `dam_id` — string (nullable)
- `damsire` — string (nullable)
- `damsire_id` — string (nullable)
- `name` — string (nullable)
- `sire` — string (nullable)
- `sire_id` — string (nullable)

### HorseAges
- `horse_age` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### HorseDistanceTimeAnalysis
- `id` — string *(req)*
- `horse` — string *(req)*
- `sire` — string *(req)*
- `sire_id` — string *(req)*
- `dam` — string *(req)*
- `dam_id` — string *(req)*
- `damsire` — string *(req)*
- `damsire_id` — string *(req)*
- `total_runs` — integer *(req)*
- `distances` — array<Distances> *(req)*
- `query` — array<array<any>> *(req)*

### HorsePool
- `pool_type_name` — string (nullable)
- `amount` — string (nullable)
- `fractional_odds` — string (nullable)
- `dollar` — string (nullable)

### HorsePro
- `id` — string *(req)*
- `breeder` — string (nullable)
- `colour` — string (nullable)
- `colour_code` — string (nullable)
- `dam` — string (nullable)
- `dam_id` — string (nullable)
- `damsire` — string (nullable)
- `damsire_id` — string (nullable)
- `dob` — string (nullable)
- `name` — string (nullable)
- `sex` — string (nullable)
- `sex_code` — string (nullable)
- `sire` — string (nullable)
- `sire_id` — string (nullable)

### Horses
- `search_results` — array<Horse> *(req)*

### JockeyCourseAnalysis
- `id` — string *(req)*
- `jockey` — string *(req)*
- `total_rides` — integer *(req)*
- `courses` — array<app__models__jockeys__Course> *(req)*
- `query` — array<array<any>> *(req)*

### JockeyDistanceAnalysis
- `id` — string *(req)*
- `jockey` — string *(req)*
- `total_rides` — integer *(req)*
- `distances` — array<app__models__jockeys__Distance> *(req)*
- `query` — array<array<any>> *(req)*

### JockeyOwnerAnalysis
- `id` — string *(req)*
- `jockey` — string *(req)*
- `total_rides` — integer *(req)*
- `owners` — array<app__models__jockeys__Owner> *(req)*
- `query` — array<array<any>> *(req)*

### JockeyTrainerAnalysis
- `id` — string *(req)*
- `jockey` — string *(req)*
- `total_rides` — integer *(req)*
- `trainers` — array<app__models__jockeys__Trainer> *(req)*
- `query` — array<array<any>> *(req)*

### Jockeys
- `search_results` — array<app__models__jockeys__Jockey> *(req)*

### MeetRaces
- `distance` — string (nullable)
- `class` — string (nullable)
- `race_group` — string (nullable)
- `race_name` — string (nullable)
- `race_number` — string (nullable)
- `race_status` — string (nullable)
- `off_time` — string (nullable)

### OddsHistory
- `bookmaker` — string *(req)*
- `fractional` — string *(req)*
- `decimal` — string *(req)*
- `ew_places` — string *(req)*
- `ew_denom` — string *(req)*
- `updated` — string *(req)*
- `history` — array<any> (nullable)

### OddsNoHistory
- `bookmaker` — string *(req)*
- `fractional` — string *(req)*
- `decimal` — string *(req)*
- `ew_places` — string *(req)*
- `ew_denom` — string *(req)*
- `updated` — string *(req)*

### OwnerCourseAnalysis
- `id` — string *(req)*
- `owner` — string *(req)*
- `total_runners` — integer *(req)*
- `courses` — array<app__models__owners__Course> *(req)*
- `query` — array<array<any>> *(req)*

### OwnerDistanceAnalysis
- `id` — string *(req)*
- `owner` — string *(req)*
- `total_runners` — integer *(req)*
- `distances` — array<app__models__owners__Distance> *(req)*
- `query` — array<array<any>> *(req)*

### OwnerJockeyAnalysis
- `id` — string *(req)*
- `owner` — string *(req)*
- `total_runners` — integer *(req)*
- `jockeys` — array<app__models__owners__Jockey> *(req)*
- `query` — array<array<any>> *(req)*

### OwnerTrainerAnalysis
- `id` — string *(req)*
- `owner` — string *(req)*
- `total_runners` — integer *(req)*
- `trainers` — array<app__models__owners__Trainer> *(req)*
- `query` — array<array<any>> *(req)*

### Owners
- `search_results` — array<app__models__owners__Owner> *(req)*

### Payoff
- `base_amount` — number (nullable)
- `carryover` — number (nullable)
- `number_of_rights` — integer (nullable)
- `number_of_tickets_bet` — integer (nullable)
- `payoff_amount` — string (nullable)
- `total_pool` — string (nullable)
- `wager_name` — string (nullable)
- `wager_type` — string (nullable)
- `winning_numbers` — string (nullable)

### RaceKey
- `race_number` — string (nullable)
- `day_evening` — string (nullable)

### RacePool
- `maximum_wager_amount` — number (nullable)
- `minimum_box_amount` — number (nullable)
- `minimum_wager_amount` — number (nullable)
- `minimum_wheel_amount` — number (nullable)
- `pool_code` — string (nullable)
- `pool_name` — string (nullable)
- `race_list` — string (nullable)

### RaceRunnerOdds
- `race_id` — string *(req)*
- `horse_id` — string *(req)*
- `horse` — string *(req)*
- `odds` — array<RaceRunnerOddsBookmakers> (nullable)

### RaceRunnerOddsBookmakers
- `bookmaker` — string (nullable)
- `fractional` — string (nullable)
- `decimal` — string (nullable)
- `ew_places` — string (nullable)
- `ew_denom` — string (nullable)
- `updated` — string (nullable)
- `history` — array<RaceRunnerOddsHistory> (nullable)

### RaceRunnerOddsHistory
- `changed_at` — string *(req)*
- `fractional` — string *(req)*
- `decimal` — string *(req)*

### Racecard
- `race_id` — string *(req)*
- `course` — string *(req)*
- `course_id` — string *(req)*
- `date` — string *(req)*
- `off_time` — string *(req)*
- `off_dt` — string (nullable)
- `race_name` — string *(req)*
- `distance_round` — string *(req)*
- `distance` — string *(req)*
- `distance_f` — string *(req)*
- `region` — string *(req)*
- `pattern` — string *(req)*
- `sex_restriction` — string (nullable)
- `race_class` — string *(req)*
- `type` — string *(req)*
- `age_band` — string *(req)*
- `rating_band` — string *(req)*
- `prize` — string *(req)*
- `field_size` — string *(req)*
- `going_detailed` — string (nullable) *(req)*
- `rail_movements` — string (nullable) *(req)*
- `stalls` — string (nullable) *(req)*
- `weather` — string (nullable) *(req)*
- `going` — string *(req)*
- `surface` — string (nullable) *(req)*
- `runners` — array<app__models__racecards__Runner> *(req)*
- `big_race` — boolean (nullable)
- `is_abandoned` — boolean (nullable)
- `race_status` — string (nullable)

### RacecardBasic
- `race_id` — string *(req)*
- `course` — string *(req)*
- `date` — string *(req)*
- `off_time` — string *(req)*
- `off_dt` — string (nullable)
- `race_name` — string *(req)*
- `distance_f` — string *(req)*
- `region` — string *(req)*
- `pattern` — string *(req)*
- `race_class` — string *(req)*
- `type` — string *(req)*
- `age_band` — string *(req)*
- `rating_band` — string *(req)*
- `sex_restriction` — string (nullable)
- `prize` — string *(req)*
- `field_size` — string *(req)*
- `going` — string *(req)*
- `surface` — string (nullable) *(req)*
- `runners` — array<app__models__racecards__RunnerBasic> *(req)*
- `race_status` — string (nullable)

### RacecardOdds
- `race_id` — string *(req)*
- `course` — string *(req)*
- `course_id` — string *(req)*
- `date` — string *(req)*
- `off_time` — string *(req)*
- `off_dt` — string (nullable)
- `race_name` — string *(req)*
- `distance_round` — string *(req)*
- `distance` — string *(req)*
- `distance_f` — string *(req)*
- `region` — string *(req)*
- `pattern` — string *(req)*
- `sex_restriction` — string (nullable)
- `race_class` — string *(req)*
- `type` — string *(req)*
- `age_band` — string *(req)*
- `rating_band` — string *(req)*
- `prize` — string *(req)*
- `field_size` — string *(req)*
- `going_detailed` — string (nullable) *(req)*
- `rail_movements` — string (nullable) *(req)*
- `stalls` — string (nullable) *(req)*
- `weather` — string (nullable) *(req)*
- `going` — string *(req)*
- `surface` — string (nullable) *(req)*
- `jumps` — string (nullable)
- `runners` — array<app__models__racecards__RunnerOdds> *(req)*
- `big_race` — boolean (nullable)
- `is_abandoned` — boolean (nullable)
- `tip` — string (nullable)
- `verdict` — string (nullable)
- `betting_forecast` — string (nullable)
- `race_status` — string (nullable)

### RacecardOddsPro
- `race_id` — string *(req)*
- `course` — string *(req)*
- `course_id` — string *(req)*
- `date` — string *(req)*
- `off_time` — string *(req)*
- `off_dt` — string (nullable)
- `race_name` — string *(req)*
- `distance_round` — string *(req)*
- `distance` — string *(req)*
- `distance_f` — string *(req)*
- `region` — string *(req)*
- `pattern` — string *(req)*
- `sex_restriction` — string (nullable)
- `race_class` — string *(req)*
- `type` — string *(req)*
- `age_band` — string *(req)*
- `rating_band` — string *(req)*
- `prize` — string *(req)*
- `field_size` — string *(req)*
- `going_detailed` — string (nullable) *(req)*
- `rail_movements` — string (nullable) *(req)*
- `stalls` — string (nullable) *(req)*
- `weather` — string (nullable) *(req)*
- `going` — string *(req)*
- `surface` — string (nullable) *(req)*
- `jumps` — string (nullable)
- `runners` — array<RunnerOddsPro> *(req)*
- `big_race` — boolean (nullable)
- `is_abandoned` — boolean (nullable)
- `tip` — string (nullable)
- `verdict` — string (nullable)
- `betting_forecast` — string (nullable)
- `race_status` — string (nullable)

### RacecardSummary
- `date` — string *(req)*
- `region` — string *(req)*
- `course_id` — string *(req)*
- `course` — string *(req)*
- `race_id` — string *(req)*
- `race_name` — string *(req)*
- `race_class` — string *(req)*
- `off_time` — string *(req)*
- `off_dt` — string (nullable)
- `big_race` — boolean (nullable)
- `is_abandoned` — boolean (nullable)

### RacecardsBasicPage
- `racecards` — array<RacecardBasic> *(req)*
- `total` — integer *(req)*
- `limit` — integer *(req)*
- `skip` — integer *(req)*
- `query` — array<array<any>> *(req)*

### RacecardsOddsPage
- `racecards` — array<RacecardOdds> *(req)*
- `total` — integer *(req)*
- `limit` — integer *(req)*
- `skip` — integer *(req)*
- `query` — array<array<any>> *(req)*

### RacecardsOddsProPage
- `racecards` — array<RacecardOddsPro> *(req)*
- `total` — integer *(req)*
- `limit` — integer *(req)*
- `skip` — integer *(req)*
- `query` — array<array<any>> *(req)*

### RacecardsPage
- `racecards` — array<Racecard> *(req)*
- `total` — integer *(req)*
- `limit` — integer *(req)*
- `skip` — integer *(req)*
- `query` — array<array<any>> *(req)*

### RacecardsSummary
- `racecard_summaries` — array<RacecardSummary> *(req)*
- `query` — array<array<any>> *(req)*

### Races
- `races` — array<app__models__aus_races__Race> *(req)*

### Region
- `region` — string *(req)*
- `region_code` — string *(req)*

### ResultBasic
- `race_id` — string *(req)*
- `date` — string *(req)*
- `region` — string *(req)*
- `course` — string *(req)*
- `course_id` — string *(req)*
- `off` — string *(req)*
- `off_dt` — string (nullable)
- `race_name` — string *(req)*
- `type` — string *(req)*
- `class` — string *(req)*
- `pattern` — string *(req)*
- `rating_band` — string *(req)*
- `age_band` — string *(req)*
- `sex_rest` — string *(req)*
- `dist` — string *(req)*
- `dist_y` — string *(req)*
- `dist_m` — string *(req)*
- `dist_f` — string *(req)*
- `going` — string *(req)*
- `surface` — string (nullable)
- `jumps` — string (nullable)
- `runners` — array<app__models__result__RunnerBasic> *(req)*
- `winning_time_detail` — string (nullable)
- `comments` — string (nullable)
- `non_runners` — string (nullable)
- `tote_win` — string (nullable)
- `tote_pl` — string (nullable)
- `tote_ex` — string (nullable)
- `tote_csf` — string (nullable)
- `tote_tricast` — string (nullable)
- `tote_trifecta` — string (nullable)

### ResultFree
- `race_id` — string *(req)*
- `course` — string *(req)*
- `date` — string *(req)*
- `off` — string *(req)*
- `off_dt` — string (nullable)
- `race_name` — string *(req)*
- `dist_f` — string *(req)*
- `region` — string *(req)*
- `pattern` — string *(req)*
- `class` — string *(req)*
- `type` — string *(req)*
- `age_band` — string *(req)*
- `rating_band` — string *(req)*
- `sex_rest` — string *(req)*
- `going` — string *(req)*
- `surface` — string (nullable)
- `runners` — array<RunnerFree> *(req)*

### ResultStandard
- `race_id` — string *(req)*
- `date` — string *(req)*
- `region` — string *(req)*
- `course` — string *(req)*
- `course_id` — string *(req)*
- `off` — string *(req)*
- `off_dt` — string (nullable)
- `race_name` — string *(req)*
- `type` — string *(req)*
- `class` — string *(req)*
- `pattern` — string *(req)*
- `rating_band` — string *(req)*
- `age_band` — string *(req)*
- `sex_rest` — string *(req)*
- `dist` — string *(req)*
- `dist_y` — string *(req)*
- `dist_m` — string *(req)*
- `dist_f` — string *(req)*
- `going` — string *(req)*
- `surface` — string (nullable)
- `jumps` — string (nullable)
- `runners` — array<RunnerStandard> *(req)*
- `winning_time_detail` — string (nullable)
- `comments` — string (nullable)
- `non_runners` — string (nullable)
- `tote_win` — string (nullable)
- `tote_pl` — string (nullable)
- `tote_ex` — string (nullable)
- `tote_csf` — string (nullable)
- `tote_tricast` — string (nullable)
- `tote_trifecta` — string (nullable)

### Results
- `meet_id` — string *(req)*
- `track_id` — string *(req)*
- `track_name` — string *(req)*
- `country` — string *(req)*
- `date` — string *(req)*
- `races` — array<app__models__na_results__Race> (nullable)
- `weather` — app__models__na_results__Weather (nullable)

### ResultsBasicPage
- `results` — array<ResultBasic> (nullable) *(req)*
- `total` — integer *(req)*
- `limit` — integer *(req)*
- `skip` — integer *(req)*
- `query` — array<array<any>> *(req)*

### ResultsFreePage
- `results` — array<ResultFree> (nullable) *(req)*
- `total` — integer *(req)*
- `limit` — integer *(req)*
- `skip` — integer *(req)*
- `query` — array<array<any>> *(req)*

### ResultsStandardPage
- `results` — array<ResultStandard> (nullable) *(req)*
- `total` — integer *(req)*
- `limit` — integer *(req)*
- `skip` — integer *(req)*
- `query` — array<array<any>> *(req)*

### RunnerFree
- `horse_id` — string *(req)*
- `horse` — string *(req)*
- `age` — string *(req)*
- `sex` — string *(req)*
- `number` — string *(req)*
- `position` — string *(req)*
- `draw` — string *(req)*
- `weight` — string *(req)*
- `weight_lbs` — string *(req)*
- `headgear` — string *(req)*
- `or` — string *(req)*
- `jockey` — string *(req)*
- `jockey_id` — string *(req)*
- `trainer` — string *(req)*
- `trainer_id` — string *(req)*
- `owner` — string *(req)*
- `owner_id` — string *(req)*
- `sire` — string *(req)*
- `sire_id` — string *(req)*
- `dam` — string *(req)*
- `dam_id` — string *(req)*
- `damsire` — string *(req)*
- `damsire_id` — string *(req)*

### RunnerMedical
- `date` — string (nullable)
- `type` — string (nullable)

### RunnerOddsPro
- `horse_id` — string *(req)*
- `horse` — string *(req)*
- `dob` — string (nullable) *(req)*
- `age` — string (nullable) *(req)*
- `sex` — string (nullable) *(req)*
- `sex_code` — string (nullable) *(req)*
- `colour` — string (nullable) *(req)*
- `region` — string (nullable) *(req)*
- `breeder` — string (nullable) *(req)*
- `dam` — string *(req)*
- `dam_id` — string *(req)*
- `dam_region` — string (nullable)
- `sire` — string *(req)*
- `sire_id` — string *(req)*
- `sire_region` — string (nullable)
- `damsire` — string *(req)*
- `damsire_id` — string *(req)*
- `damsire_region` — string (nullable)
- `trainer` — string *(req)*
- `trainer_id` — string *(req)*
- `trainer_location` — string (nullable)
- `trainer_14_days` — RunnerTrainer14Days (nullable)
- `owner` — string *(req)*
- `owner_id` — string *(req)*
- `prev_trainers` — array<RunnerPrevTrainer> (nullable)
- `prev_owners` — array<RunnerPrevOwner> (nullable)
- `comment` — string (nullable)
- `spotlight` — string (nullable)
- `quotes` — array<RunnerQuote> (nullable)
- `stable_tour` — array<RunnerStableTour> (nullable)
- `medical` — array<RunnerMedical> (nullable)
- `number` — string *(req)*
- `draw` — string *(req)*
- `headgear` — string (nullable)
- `headgear_run` — string (nullable)
- `wind_surgery` — string (nullable)
- `wind_surgery_run` — string (nullable)
- `past_results_flags` — array<string> (nullable)
- `lbs` — string *(req)*
- `ofr` — string *(req)*
- `rpr` — string *(req)*
- `ts` — string *(req)*
- `jockey` — string *(req)*
- `jockey_id` — string *(req)*
- `silk_url` — string (nullable)
- `last_run` — string *(req)*
- `form` — string (nullable) *(req)*
- `trainer_rtf` — string (nullable) *(req)*
- `odds` — array<OddsHistory> (nullable)

### RunnerPrevOwner
- `owner` — string (nullable)
- `owner_id` — string (nullable)
- `change_date` — string (nullable)

### RunnerPrevTrainer
- `trainer` — string (nullable)
- `trainer_id` — string (nullable)
- `change_date` — string (nullable)

### RunnerQuote
- `date` — string (nullable)
- `horse` — string (nullable)
- `horse_id` — string (nullable)
- `race` — string (nullable)
- `race_id` — string (nullable)
- `course` — string (nullable)
- `course_id` — string (nullable)
- `distance_f` — string (nullable)
- `distance_y` — string (nullable)
- `quote` — string (nullable)

### RunnerStableTour
- `quote` — string (nullable)

### RunnerStandard
- `horse_id` — string *(req)*
- `horse` — string *(req)*
- `sp` — string *(req)*
- `sp_dec` — string *(req)*
- `bsp` — string (nullable)
- `number` — string *(req)*
- `position` — string *(req)*
- `draw` — string *(req)*
- `btn` — string *(req)*
- `ovr_btn` — string *(req)*
- `age` — string *(req)*
- `sex` — string *(req)*
- `weight` — string *(req)*
- `weight_lbs` — string *(req)*
- `headgear` — string *(req)*
- `time` — string *(req)*
- `or` — string *(req)*
- `rpr` — string *(req)*
- `tsr` — string *(req)*
- `prize` — string *(req)*
- `jockey` — string *(req)*
- `jockey_claim_lbs` — string (nullable)
- `jockey_id` — string *(req)*
- `trainer` — string *(req)*
- `trainer_id` — string *(req)*
- `owner` — string *(req)*
- `owner_id` — string *(req)*
- `sire` — string *(req)*
- `sire_id` — string *(req)*
- `dam` — string *(req)*
- `dam_id` — string *(req)*
- `damsire` — string *(req)*
- `damsire_id` — string *(req)*
- `comment` — string *(req)*
- `silk_url` — string (nullable)

### RunnerStats
- `career_prize` — string (nullable)
- `career_win_percent` — string (nullable)
- `career_place_percent` — string (nullable)
- `course_stats` — RunnerStatsBreakdown (nullable)
- `course_distance_stats` — RunnerStatsBreakdown (nullable)
- `distance_stats` — RunnerStatsBreakdown (nullable)
- `ground_firm_stats` — RunnerStatsBreakdown (nullable)
- `ground_good_stats` — RunnerStatsBreakdown (nullable)
- `ground_heavy_stats` — RunnerStatsBreakdown (nullable)
- `ground_soft_stats` — RunnerStatsBreakdown (nullable)
- `ground_aw_stats` — RunnerStatsBreakdown (nullable)
- `jockey_stats` — RunnerStatsBreakdown (nullable)
- `jumps_stats` — RunnerStatsBreakdown (nullable)
- `last_raced` — string (nullable)
- `last_ten_races_stats` — RunnerStatsBreakdown (nullable)
- `last_twelve_months_stats` — RunnerStatsBreakdown (nullable)
- `last_won` — string (nullable)
- `max_winning_distance` — string (nullable)
- `min_winning_distance` — string (nullable)

### RunnerStatsBreakdown
- `total` — string (nullable)
- `first` — string (nullable)
- `second` — string (nullable)
- `third` — string (nullable)

### RunnerTrainer14Days
- `runs` — string (nullable)
- `wins` — string (nullable)
- `percent` — string (nullable)

### Sire
- `id` — string *(req)*
- `name` — string (nullable) *(req)*

### SireClassAnalysis
- `id` — string *(req)*
- `sire` — string *(req)*
- `total_runners` — integer *(req)*
- `classes` — array<app__models__sires__Class> *(req)*
- `query` — array<array<any>> *(req)*

### SireDistanceAnalysis
- `id` — string *(req)*
- `sire` — string *(req)*
- `total_runners` — integer *(req)*
- `distances` — array<app__models__sires__Distance> *(req)*
- `query` — array<array<any>> *(req)*

### Sires
- `search_results` — array<Sire> *(req)*

### TimeData
- `minutes` — integer (nullable)
- `seconds` — integer (nullable)
- `hundredths` — integer (nullable)
- `milliseconds` — integer (nullable)
- `fifths` — integer (nullable)
- `str_fifths` — string (nullable)
- `time_in_fifths` — string (nullable)
- `time_in_hundredths` — string (nullable)

### TimesGoing
- `date` — string *(req)*
- `region` — string *(req)*
- `course` — string *(req)*
- `time` — string *(req)*
- `going` — string *(req)*
- `position` — string *(req)*

### TrainerCourseAnalysis
- `id` — string *(req)*
- `trainer` — string *(req)*
- `total_runners` — integer *(req)*
- `courses` — array<app__models__trainers__Course> *(req)*
- `query` — array<array<any>> *(req)*

### TrainerDistanceAnalysis
- `id` — string *(req)*
- `trainer` — string *(req)*
- `total_runners` — integer *(req)*
- `distances` — array<app__models__trainers__Distance> *(req)*
- `query` — array<array<any>> *(req)*

### TrainerHorseAgeAnalysis
- `id` — string *(req)*
- `trainer` — string *(req)*
- `total_runners` — integer *(req)*
- `horse_ages` — array<HorseAges> *(req)*
- `query` — array<array<any>> *(req)*

### TrainerJockeyAnalysis
- `id` — string *(req)*
- `trainer` — string *(req)*
- `total_runners` — integer *(req)*
- `jockeys` — array<app__models__trainers__Jockey> *(req)*
- `query` — array<array<any>> *(req)*

### TrainerOwnerAnalysis
- `id` — string *(req)*
- `trainer` — string *(req)*
- `total_runners` — integer *(req)*
- `owners` — array<app__models__trainers__Owner> *(req)*
- `query` — array<array<any>> *(req)*

### Trainers
- `search_results` — array<app__models__trainers__Trainer> *(req)*

### ValidationError
- `loc` — array<string|integer> *(req)*
- `msg` — string *(req)*
- `type` — string *(req)*
- `input` — any
- `ctx` — object

### WagerType
- `wager_type` — string (nullable)
- `wager_description` — string (nullable)
- `base_amount` — string (nullable)

### app__models__aus_meets__Meet
- `meet_id` — string (nullable)
- `date` — string (nullable)
- `course` — string (nullable)
- `course_id` — string (nullable)
- `races` — array<MeetRaces> *(req)*
- `state` — string (nullable)

### app__models__aus_meets__Meets
- `meets` — array<app__models__aus_meets__Meet> (nullable)

### app__models__aus_races__Race
- `course` — string (nullable)
- `course_id` — string (nullable)
- `date` — string (nullable)
- `distance` — string (nullable)
- `going` — string (nullable)
- `is_jump_out` — boolean (nullable)
- `is_trial` — boolean (nullable)
- `meet_id` — string
- `off_time` — string (nullable)
- `prizes` — array<any> (nullable)
- `prize_total` — string (nullable)
- `class` — string (nullable)
- `race_conditions` — string (nullable)
- `race_group` — string (nullable)
- `race_name` — string (nullable)
- `race_number` — string (nullable)
- `race_status` — string (nullable)
- `state` — string (nullable)
- `runners` — array<app__models__aus_races__Runner>
- `winning_time` — string (nullable)
- `winning_time_hundredths` — string (nullable)

### app__models__aus_races__Runner
- `horse_id` — string *(req)*
- `horse` — string *(req)*
- `age` — string (nullable)
- `comment` — string (nullable)
- `colour` — string (nullable)
- `dam` — string (nullable)
- `dam_id` — string (nullable)
- `draw` — string (nullable)
- `form` — string (nullable)
- `jockey` — string (nullable)
- `jockey_id` — string (nullable)
- `jockey_claim` — string (nullable)
- `margin` — string (nullable)
- `number` — string (nullable)
- `odds` — array<app__models__aus_races__RunnerOdds> (nullable)
- `owner` — string (nullable)
- `position` — string (nullable)
- `prize` — string (nullable)
- `rating` — string (nullable)
- `scratched` — boolean (nullable)
- `sex` — string (nullable)
- `silk_url` — string (nullable)
- `sire` — string (nullable)
- `sire_id` — string (nullable)
- `sp` — string (nullable)
- `stats` — RunnerStats (nullable)
- `trainer` — string (nullable)
- `trainer_id` — string (nullable)
- `weight` — string (nullable)

### app__models__aus_races__RunnerOdds
- `bookmaker` — string (nullable)
- `win_odds` — string (nullable)
- `place_odds` — string (nullable)

### app__models__courses__Course
- `id` — string *(req)*
- `course` — string *(req)*
- `region_code` — string *(req)*
- `region` — string *(req)*

### app__models__dams__Class
- `class` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__dams__Distance
- `dist` — string *(req)*
- `dist_y` — string *(req)*
- `dist_m` — string *(req)*
- `dist_f` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__damsires__Class
- `class` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__damsires__Distance
- `dist` — string *(req)*
- `dist_y` — string *(req)*
- `dist_m` — string *(req)*
- `dist_f` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__jockeys__Course
- `course` — string *(req)*
- `course_id` — string *(req)*
- `region` — string *(req)*
- `rides` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__jockeys__Distance
- `dist` — string *(req)*
- `dist_y` — string *(req)*
- `dist_m` — string *(req)*
- `dist_f` — string *(req)*
- `rides` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__jockeys__Jockey
- `id` — string *(req)*
- `name` — string (nullable) *(req)*

### app__models__jockeys__Owner
- `owner_id` — string *(req)*
- `owner` — string *(req)*
- `rides` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__jockeys__Trainer
- `trainer_id` — string *(req)*
- `trainer` — string *(req)*
- `rides` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__na_entries__Jockey
- `id` — string (nullable)
- `alias` — string (nullable)
- `first_name` — string (nullable)
- `first_name_initial` — string (nullable)
- `last_name` — string (nullable)
- `middle_name` — string (nullable)
- `type` — string (nullable)

### app__models__na_entries__Race
- `age_restriction` — string (nullable)
- `age_restriction_description` — string (nullable)
- `breed` — string (nullable)
- `changes` — array<Change> (nullable)
- `course_type` — string (nullable)
- `course_type_class` — string (nullable)
- `distance_description` — string (nullable)
- `distance_unit` — string (nullable)
- `distance_value` — integer|string (nullable)
- `grade` — string (nullable)
- `handicapper_name` — string (nullable)
- `has_finished` — boolean (nullable)
- `has_results` — boolean (nullable)
- `is_cancelled` — boolean (nullable)
- `max_claim_price` — integer|string (nullable)
- `min_claim_price` — integer|string (nullable)
- `mtp` — integer (nullable)
- `post_time` — string (nullable)
- `post_time_long` — string (nullable)
- `purse` — integer|string (nullable)
- `race_class` — string (nullable)
- `race_key` — RaceKey *(req)*
- `race_name` — string (nullable)
- `race_pools` — array<RacePool> (nullable)
- `race_restriction` — string (nullable)
- `race_restriction_description` — string (nullable)
- `race_type` — string (nullable)
- `race_type_description` — string (nullable)
- `runners` — array<app__models__na_entries__Runner> *(req)*
- `sex_restriction` — string (nullable)
- `sex_restriction_description` — string (nullable)
- `surface_description` — string (nullable)
- `time_zone` — string (nullable)
- `tote_track_id` — string (nullable)
- `track_condition` — string (nullable)
- `track_name` — string (nullable)

### app__models__na_entries__Runner
- `claiming` — integer|string (nullable)
- `coupled_type` — string (nullable)
- `dam_name` — string (nullable)
- `dam_sire_name` — string (nullable)
- `description` — string (nullable)
- `equipment` — string (nullable)
- `handicapper_name` — string (nullable)
- `horse_data_pools` — array<HorsePool> (nullable)
- `horse_name` — string (nullable)
- `jockey` — app__models__na_entries__Jockey (nullable)
- `live_odds` — string (nullable)
- `medication` — string (nullable)
- `morning_line_odds` — string (nullable)
- `post_pos` — string (nullable)
- `program_number` — string (nullable)
- `program_number_stripped` — integer (nullable)
- `registration_number` — string (nullable)
- `scratch_indicator` — string (nullable)
- `sire_name` — string (nullable)
- `trainer` — app__models__na_entries__Trainer (nullable)
- `weight` — string (nullable)

### app__models__na_entries__Trainer
- `id` — string (nullable)
- `alias` — string (nullable)
- `first_name` — string (nullable)
- `first_name_initial` — string (nullable)
- `last_name` — string (nullable)
- `middle_name` — string (nullable)
- `type` — string (nullable)

### app__models__na_entries__Weather
- `forecast_weather_description` — string (nullable)
- `forecast_high` — integer|string (nullable)
- `forecast_low` — integer|string (nullable)
- `forecast_precipitation` — integer|string (nullable)
- `current_weather_description` — string (nullable)

### app__models__na_meets__Meet
- `country` — string *(req)*
- `date` — string *(req)*
- `meet_id` — string *(req)*
- `track_id` — string *(req)*
- `track_name` — string *(req)*

### app__models__na_meets__Meets
- `meets` — array<app__models__na_meets__Meet> (nullable)
- `limit` — integer *(req)*
- `skip` — integer *(req)*
- `query` — array<array<any>> *(req)*

### app__models__na_results__Race
- `age_restriction` — string (nullable)
- `age_restriction_description` — string (nullable)
- `also_ran` — string|array<any> (nullable)
- `breed` — string (nullable)
- `distance_description` — string (nullable)
- `distance_unit` — string (nullable)
- `distance_value` — integer|string (nullable)
- `fraction` — Fraction (nullable)
- `grade` — string (nullable)
- `maximum_claim_price` — string (nullable)
- `minimum_claim_price` — string (nullable)
- `off_time` — integer (nullable)
- `payoffs` — array<Payoff> (nullable)
- `post_time` — string (nullable)
- `post_time_long` — integer (nullable)
- `race_class` — string (nullable)
- `race_key` — RaceKey (nullable)
- `race_name` — string (nullable)
- `race_restriction` — string (nullable)
- `race_restriction_description` — string (nullable)
- `race_type` — string (nullable)
- `race_type_description` — string (nullable)
- `runners` — array<app__models__na_results__Runner> (nullable)
- `scratches` — array<string (nullable)> (nullable)
- `sex_restriction` — string (nullable)
- `sex_restriction_description` — string (nullable)
- `surface` — string (nullable)
- `surface_description` — string (nullable)
- `time_zone` — string (nullable)
- `total_purse` — string (nullable)
- `track_condition_description` — string (nullable)
- `track_name` — string (nullable)
- `wager_types` — array<WagerType> (nullable)

### app__models__na_results__Runner
- `breeder_name` — string (nullable)
- `horse_name` — string (nullable)
- `jockey_first_name` — string (nullable)
- `jockey_first_name_initial` — string (nullable)
- `jockey_last_name` — string (nullable)
- `owner_first_name` — string (nullable)
- `owner_last_name` — string (nullable)
- `place_payoff` — number (nullable)
- `program_number` — string (nullable)
- `program_number_stripped` — integer (nullable)
- `show_payoff` — number (nullable)
- `sire_name` — string (nullable)
- `trainer_first_name` — string (nullable)
- `trainer_last_name` — string (nullable)
- `weight_carried` — string (nullable)
- `win_payoff` — number (nullable)

### app__models__na_results__Weather
- `current_temperature` — string (nullable)
- `current_weather_description` — string (nullable)
- `date` — string (nullable)
- `forecast_high` — integer|string (nullable)
- `forecast_low` — integer|string (nullable)
- `forecast_precipitation` — integer|string (nullable)
- `forecast_weather_description` — string (nullable)

### app__models__owners__Course
- `course` — string *(req)*
- `course_id` — string *(req)*
- `region` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__owners__Distance
- `dist` — string *(req)*
- `dist_y` — string *(req)*
- `dist_m` — string *(req)*
- `dist_f` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__owners__Jockey
- `jockey_id` — string *(req)*
- `jockey` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__owners__Owner
- `id` — string *(req)*
- `name` — string (nullable) *(req)*

### app__models__owners__Trainer
- `trainer_id` — string *(req)*
- `trainer` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__racecards__Runner
- `horse_id` — string *(req)*
- `horse` — string *(req)*
- `dob` — string (nullable) *(req)*
- `age` — string (nullable) *(req)*
- `sex` — string (nullable) *(req)*
- `sex_code` — string (nullable) *(req)*
- `colour` — string (nullable) *(req)*
- `region` — string (nullable) *(req)*
- `breeder` — string (nullable) *(req)*
- `dam` — string *(req)*
- `dam_id` — string *(req)*
- `dam_region` — string (nullable)
- `sire` — string *(req)*
- `sire_id` — string *(req)*
- `sire_region` — string (nullable)
- `damsire` — string *(req)*
- `damsire_id` — string *(req)*
- `damsire_region` — string (nullable)
- `trainer` — string *(req)*
- `trainer_id` — string *(req)*
- `trainer_location` — string (nullable)
- `trainer_14_days` — RunnerTrainer14Days (nullable)
- `owner` — string *(req)*
- `owner_id` — string *(req)*
- `prev_trainers` — array<RunnerPrevTrainer> (nullable)
- `prev_owners` — array<RunnerPrevOwner> (nullable)
- `comment` — string (nullable)
- `spotlight` — string (nullable)
- `quotes` — array<RunnerQuote> (nullable)
- `stable_tour` — array<RunnerStableTour> (nullable)
- `medical` — array<RunnerMedical> (nullable)
- `number` — string *(req)*
- `draw` — string *(req)*
- `headgear` — string (nullable)
- `headgear_run` — string (nullable)
- `wind_surgery` — string (nullable)
- `wind_surgery_run` — string (nullable)
- `past_results_flags` — array<string> (nullable)
- `lbs` — string *(req)*
- `ofr` — string *(req)*
- `rpr` — string *(req)*
- `ts` — string *(req)*
- `jockey` — string *(req)*
- `jockey_id` — string *(req)*
- `silk_url` — string (nullable)
- `last_run` — string *(req)*
- `form` — string (nullable) *(req)*
- `trainer_rtf` — string (nullable) *(req)*

### app__models__racecards__RunnerBasic
- `horse` — string *(req)*
- `horse_id` — string *(req)*
- `age` — string *(req)*
- `sex` — string (nullable) *(req)*
- `sex_code` — string (nullable) *(req)*
- `colour` — string (nullable) *(req)*
- `region` — string *(req)*
- `dam` — string *(req)*
- `dam_id` — string *(req)*
- `sire` — string *(req)*
- `sire_id` — string *(req)*
- `damsire` — string *(req)*
- `damsire_id` — string *(req)*
- `trainer` — string *(req)*
- `trainer_id` — string *(req)*
- `owner` — string *(req)*
- `owner_id` — string *(req)*
- `number` — string *(req)*
- `draw` — string *(req)*
- `headgear` — string (nullable) *(req)*
- `lbs` — string *(req)*
- `ofr` — string *(req)*
- `jockey` — string *(req)*
- `jockey_id` — string *(req)*
- `last_run` — string *(req)*
- `form` — string (nullable) *(req)*

### app__models__racecards__RunnerOdds
- `horse_id` — string *(req)*
- `horse` — string *(req)*
- `dob` — string (nullable) *(req)*
- `age` — string (nullable) *(req)*
- `sex` — string (nullable) *(req)*
- `sex_code` — string (nullable) *(req)*
- `colour` — string (nullable) *(req)*
- `region` — string (nullable) *(req)*
- `breeder` — string (nullable) *(req)*
- `dam` — string *(req)*
- `dam_id` — string *(req)*
- `dam_region` — string (nullable)
- `sire` — string *(req)*
- `sire_id` — string *(req)*
- `sire_region` — string (nullable)
- `damsire` — string *(req)*
- `damsire_id` — string *(req)*
- `damsire_region` — string (nullable)
- `trainer` — string *(req)*
- `trainer_id` — string *(req)*
- `trainer_location` — string (nullable)
- `trainer_14_days` — RunnerTrainer14Days (nullable)
- `owner` — string *(req)*
- `owner_id` — string *(req)*
- `prev_trainers` — array<RunnerPrevTrainer> (nullable)
- `prev_owners` — array<RunnerPrevOwner> (nullable)
- `comment` — string (nullable)
- `spotlight` — string (nullable)
- `quotes` — array<RunnerQuote> (nullable)
- `stable_tour` — array<RunnerStableTour> (nullable)
- `medical` — array<RunnerMedical> (nullable)
- `number` — string *(req)*
- `draw` — string *(req)*
- `headgear` — string (nullable)
- `headgear_run` — string (nullable)
- `wind_surgery` — string (nullable)
- `wind_surgery_run` — string (nullable)
- `past_results_flags` — array<string> (nullable)
- `lbs` — string *(req)*
- `ofr` — string *(req)*
- `rpr` — string *(req)*
- `ts` — string *(req)*
- `jockey` — string *(req)*
- `jockey_id` — string *(req)*
- `silk_url` — string (nullable)
- `last_run` — string *(req)*
- `form` — string (nullable) *(req)*
- `trainer_rtf` — string (nullable) *(req)*
- `odds` — array<OddsNoHistory> (nullable)

### app__models__result__RunnerBasic
- `horse_id` — string *(req)*
- `horse` — string *(req)*
- `sp` — string *(req)*
- `sp_dec` — string *(req)*
- `number` — string *(req)*
- `position` — string *(req)*
- `draw` — string *(req)*
- `btn` — string *(req)*
- `ovr_btn` — string *(req)*
- `age` — string *(req)*
- `sex` — string *(req)*
- `weight` — string *(req)*
- `weight_lbs` — string *(req)*
- `headgear` — string *(req)*
- `time` — string *(req)*
- `or` — string *(req)*
- `rpr` — string *(req)*
- `tsr` — string *(req)*
- `prize` — string *(req)*
- `jockey` — string *(req)*
- `jockey_claim_lbs` — string (nullable)
- `jockey_id` — string *(req)*
- `trainer` — string *(req)*
- `trainer_id` — string *(req)*
- `owner` — string *(req)*
- `owner_id` — string *(req)*
- `sire` — string *(req)*
- `sire_id` — string *(req)*
- `dam` — string *(req)*
- `dam_id` — string *(req)*
- `damsire` — string *(req)*
- `damsire_id` — string *(req)*
- `comment` — string *(req)*
- `silk_url` — string (nullable)

### app__models__sires__Class
- `class` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__sires__Distance
- `dist` — string *(req)*
- `dist_y` — string *(req)*
- `dist_m` — string *(req)*
- `dist_f` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__trainers__Course
- `course` — string *(req)*
- `course_id` — string *(req)*
- `region` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__trainers__Distance
- `dist` — string *(req)*
- `dist_y` — string *(req)*
- `dist_m` — string *(req)*
- `dist_f` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__trainers__Jockey
- `jockey_id` — string *(req)*
- `jockey` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__trainers__Owner
- `owner_id` — string *(req)*
- `owner` — string *(req)*
- `runners` — integer *(req)*
- `1st` — integer *(req)*
- `2nd` — integer *(req)*
- `3rd` — integer *(req)*
- `4th` — integer *(req)*
- `a/e` — number *(req)*
- `win_%` — number *(req)*
- `1_pl` — number *(req)*

### app__models__trainers__Trainer
- `id` — string *(req)*
- `name` — string (nullable) *(req)*
