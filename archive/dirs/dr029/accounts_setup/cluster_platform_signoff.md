# Cluster & Platform Picklists — Sign-off Sheet

**For:** accounts-setup revision (book `ownership_cluster` and
`platform` move from free-text to dropdowns).
**Drafted:** Session 152 (2026-06-16, Adelaide), from desktop
research (gobet.com.au platform mapping + aussportsbetting ownership
structure, both current to June 2026).
**Status:** operator declined line-by-line review ("trust your
judgement") — locked as drafted, with the "verify owner" flags below
kept visible. Maintenance: no periodic review; research a genuinely
**unknown** book at registration time to confirm relatedness.

---

## Platform options (7)

The shared white-label interface a book runs on. Books on the same
platform share odds, promotions, and — critically — the provider's
risk engine.

1. **BetMakers**
2. **GenerationWeb**
3. **Punterstech**
4. **BetCloud**
5. **ApolloTech**
6. **BetEngine**
7. **Custom** — book runs its own software (Sportsbet, bet365,
   Ladbrokes, Neds, betr, Dabble, Unibet, Palmerbet, TAB, PlayUp,
   Bet Right, Betfair)

> Platform is **mutable** — books re-platform over time, and new
> providers appear. The field is stored as text constrained to this
> list (not a hard DB enum), so the list can be extended without a
> schema change.

## Cluster options (major-owner granularity)

The corporate owner. Kept at major-owner level — that is exactly where
the protect-vs-harvest line sits (see strategy note).

1. **Entain** (Ladbrokes, Neds)
2. **Flutter** (Sportsbet)
3. **Tabcorp** (TAB)
4. **bet365**
5. **betr / BlueBet** (betr)
6. **Crown / Blackstone** (Betfair)
7. **PlayUp** (NextBet) — *verify, recent rebrand*
8. **PointsBet** — *verify owner, recent consolidation*
9. **Independent** — single-brand owners (everything else)

---

## Book → platform reference map (research, June 2026)

Reference only (not all of these are Tim's accounts). Use it to fill
the platform field correctly as books are registered.

**BetMakers (~40):** RealBookie, Swiftbet, Next2Go, Punt123, PuntX,
BetEstate, BetLocal, MarantelliBet, CrownBet, BossBet, UpYaGo,
BetYouCan, BaggyBet, OKEBET, PremiumBet, ReadyBet, StableBet,
RobWaterhouse, Chasebet, PlayWest, BetAus, BetDash, BetGold, Betit,
BetLegends, BetSupreme, BetZooka, DiamondBet, EarlyCrow, FatBet,
KnuckleBet, Multis, PicnicBet, PonyBet, TerryBet, UPCoz, WishBet,
BallrBet.

**GenerationWeb (~26):** EliteBet, Colossalbet, WinnersBet, GoldBet,
HavaBet, MidasBet, DashBet, PandaBet, NinjaBet, OnlyBets, BetNow,
BetNova, BetBetBet, JimmyBet, JustBet, LetsBet, MyBet, PuntNow,
PuntZone, UltraBet, VicBet, BoostBet, BetDogs, BetM, Allbets, HOT Bet.

**Punterstech (~22):** BetChamps, Betfocus, TeamBet, Xbet, TradieBet,
Star Sports Australia, LightningBet, Bet Alpha, BetReal, BetVista,
BlondeBet, Chasebet, CashCage, DragonBet, MillennialBet, MintBet,
Topbet, TrueBet, WizBet, BetBuzz, BetBunker, Betblitz.

**BetCloud (~12):** EpicOdds, BetGalaxy, TitanBet, ChromaBet, WellBet,
Bet777, BetProfessor, GoldenBet888, JuicyBet, QuestBet, TempleBet,
VikingBet.

**ApolloTech:** 123bet, Betbox, BetShop, Favbet, PuntSport, BearBet.

**BetEngine:** GRSBet, LASERBET.

**Custom / own:** Sportsbet, bet365, Ladbrokes, Neds, betr, Dabble,
Unibet, Palmerbet, TAB, PlayUp, Bet Right, Betfair, Draftstars.

> Note: Chasebet appears under two providers in the source — a sign
> of a recent re-platform. Confirm against the live site when it is
> registered.
