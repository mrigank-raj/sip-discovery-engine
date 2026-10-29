# Golden set: relevance only

Stratified for coverage, not proportional to volume; 20 items, so every rate rests on very few items.

- Agreement: 70% (14/20)
- Engine said relevant and you agreed (precision): 50% (6/12)
- You said relevant and the engine agreed (recall): 100% (6/6)
- By source: appstore 100% (4/4); play 50% (2/4); reddit 75% (3/4); tradingqna 50% (2/4); youtube 75% (3/4)
- By prefilter group: stop_or_fail 60% (3/5); returns 80% (8/10); sip_or_mf 60% (3/5)

## Relevance, item by item

| # | source | group | you | engine | engine family | whose | language | confidence |
|---|---|---|---|---|---|---|---|---|
| G1 | appstore | returns | no | no | other | no_one | english | high |
| G2 **x** | play | returns | no | yes | sip_or_mf_journey | own | english | high |
| G3 **x** | reddit | returns | no | yes | sip_or_mf_journey | named_person | english | high |
| G4 | tradingqna | returns | no | no | other | no_one | english | high |
| G5 | youtube | returns | yes | yes | sip_or_mf_journey | own | hinglish | high |
| G6 | appstore | sip_or_mf | no | no | other | no_one | english | high |
| G7 | play | sip_or_mf | no | no | other | no_one | english | high |
| G8 | reddit | sip_or_mf | no | no | other | someone_else | english | high |
| G9 **x** | tradingqna | sip_or_mf | no | yes | sip_or_mf_journey | own | english | medium |
| G10 **x** | youtube | sip_or_mf | no | yes | sip_or_mf_journey | own | english | high |
| G11 | appstore | stop_or_fail | yes | yes | sip_or_mf_journey | named_person | english | high |
| G12 **x** | play | stop_or_fail | no | yes | sip_or_mf_journey | own | english | medium |
| G13 | reddit | stop_or_fail | yes | yes | sip_or_mf_journey | own | english | high |
| G14 **x** | tradingqna | stop_or_fail | no | yes | sip_or_mf_journey | own | english | medium |
| G15 | youtube | stop_or_fail | yes | yes | sip_or_mf_journey | own | hinglish | high |
| G16 | appstore | returns | no | no | app_bug_or_support | no_one | english | high |
| G17 | play | returns | no | no | other | no_one | english | high |
| G18 | reddit | returns | yes | yes | sip_or_mf_journey | own | english | high |
| G19 | tradingqna | returns | no | no | other | no_one | english | high |
| G20 | youtube | returns | yes | yes | sip_or_mf_journey | own | english | high |

## Relevance disagreements

### G2 (play, returns): you no, engine yes as `sip_or_mf_journey` (high confidence)

> Your app shows me only historic XIRR returns of entire MF portfolio but not able to see my last 3M, 6M, 1Y, 3Y XIRR returns in MF . Kindly add this like other apps Zerodha, Groww.

### G3 (reddit, returns): you no, engine yes as `sip_or_mf_journey` (high confidence)

> Also honorable mention is the GST charged on each premium payment. Conveniently, nobody talks about that, and not even in your calculations. Add it, IIRC 4.5% on first premium payment, and 2.5% on subsequent payments, and your XIRR drops by 2-3% more.

### G9 (tradingqna, sip_or_mf): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> [Feature request] Need option to select only mutual funds in Console
>
> Currently we see option to exclude the mutual funds in “Holdings” page which enables to select just stocks.
>
> Similarly I am looking for option to select just MF holdings for sector wise allocation and stocks they are holding.

### G10 (youtube, sip_or_mf): you no, engine yes as `sip_or_mf_journey` (high confidence)

> DSP Small Cap Fund - Direct Plan - Growth

### G12 (play, stop_or_fail): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> if you r using groww for only mf don't upgrade to dmat. otherwise u will redeem your money only thg Grow. that fund's app redeem money more faster than grow. grow takes 2 day more time

### G14 (tradingqna, stop_or_fail): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> Does it give detailed  CG statement with for each quarter as mandated by tax forms?

