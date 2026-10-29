# Golden set: relevance only

Stratified for coverage, not proportional to volume; 20 items, so every rate rests on very few items.

- Agreement: 80% (16/20)
- Engine said relevant and you agreed (precision): 67% (4/6)
- You said relevant and the engine agreed (recall): 67% (4/6)
- By source: appstore 100% (4/4); play 100% (4/4); reddit 75% (3/4); tradingqna 75% (3/4); youtube 50% (2/4)
- By prefilter group: stop_or_fail 60% (3/5); returns 80% (8/10); sip_or_mf 100% (5/5)

## Relevance, item by item

| # | source | group | you | engine | engine family | whose | language | confidence |
|---|---|---|---|---|---|---|---|---|
| G1 | appstore | returns | no | no | other | someone_else | english | medium |
| G2 | play | returns | no | no | other | own | english | high |
| G3 **x** | reddit | returns | no | yes | sip_or_mf_journey | named_person | english | medium |
| G4 | tradingqna | returns | no | no | other | no_one | english | high |
| G5 **x** | youtube | returns | yes | no | sip_or_mf_journey | someone_else | hinglish | medium |
| G6 | appstore | sip_or_mf | no | no | other | someone_else | english | medium |
| G7 | play | sip_or_mf | no | no | other | no_one | english | medium |
| G8 | reddit | sip_or_mf | no | no | other | someone_else | english | high |
| G9 | tradingqna | sip_or_mf | no | no | other | own | english | high |
| G10 | youtube | sip_or_mf | no | no | other | no_one | english | high |
| G11 | appstore | stop_or_fail | yes | yes | sip_or_mf_journey | named_person | english | high |
| G12 | play | stop_or_fail | no | no | other | someone_else | hinglish | high |
| G13 | reddit | stop_or_fail | yes | yes | sip_or_mf_journey | own | english | high |
| G14 **x** | tradingqna | stop_or_fail | no | yes | sip_or_mf_journey | own | english | medium |
| G15 **x** | youtube | stop_or_fail | yes | no | sip_or_mf_journey | someone_else | hinglish | medium |
| G16 | appstore | returns | no | no | app_bug_or_support | no_one | english | medium |
| G17 | play | returns | no | no | other | no_one | english | high |
| G18 | reddit | returns | yes | yes | sip_or_mf_journey | own | english | high |
| G19 | tradingqna | returns | no | no | charges_or_fees | someone_else | english | medium |
| G20 | youtube | returns | yes | yes | sip_or_mf_journey | own | english | high |

## Relevance disagreements

### G3 (reddit, returns): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> Also honorable mention is the GST charged on each premium payment. Conveniently, nobody talks about that, and not even in your calculations. Add it, IIRC 4.5% on first premium payment, and 2.5% on subsequent payments, and your XIRR drops by 2-3% more.

### G5 (youtube, returns): you yes, engine no as `sip_or_mf_journey` (medium confidence)

> Agar har month sip kar rahe hai to aage chal kar agar return nahi dega to jo paisa invest kiye hai wo to milega na

### G14 (tradingqna, stop_or_fail): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> Does it give detailed  CG statement with for each quarter as mandated by tax forms?

### G15 (youtube, stop_or_fail): you yes, engine no as `sip_or_mf_journey` (medium confidence)

> Once we cancel the SIP, can we restart it when we want?

