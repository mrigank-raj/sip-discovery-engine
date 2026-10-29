# Golden set: relevance only

Stratified for coverage, not proportional to volume; 20 items, so every rate rests on very few items.

- Agreement: 65% (13/20)
- Engine said relevant and you agreed (precision): 60% (9/15)
- You said relevant and the engine agreed (recall): 90% (9/10)
- By source: appstore 75% (3/4); play 50% (2/4); reddit 75% (3/4); tradingqna 50% (2/4); youtube 75% (3/4)
- By prefilter group: stop_or_fail 80% (4/5); returns 80% (8/10); sip_or_mf 20% (1/5)

## Relevance, item by item

| # | source | group | you | engine | engine family | language | confidence |
|---|---|---|---|---|---|---|---|
| G1 | appstore | returns | yes | yes | sip_or_mf_journey | english | medium |
| G2 | play | returns | yes | yes | sip_or_mf_journey | english | high |
| G3 | reddit | returns | no | no | other | english | medium |
| G4 | tradingqna | returns | no | no | other | english | high |
| G5 | youtube | returns | yes | yes | sip_or_mf_journey | hinglish | high |
| G6 | appstore | sip_or_mf | no | no | other | english | medium |
| G7 **x** | play | sip_or_mf | no | yes | sip_or_mf_journey | english | medium |
| G8 **x** | reddit | sip_or_mf | no | yes | sip_or_mf_journey | english | medium |
| G9 **x** | tradingqna | sip_or_mf | no | yes | sip_or_mf_journey | english | medium |
| G10 **x** | youtube | sip_or_mf | no | yes | sip_or_mf_journey | english | medium |
| G11 | appstore | stop_or_fail | yes | yes | sip_or_mf_journey | english | high |
| G12 **x** | play | stop_or_fail | no | yes | sip_or_mf_journey | english | high |
| G13 | reddit | stop_or_fail | yes | yes | sip_or_mf_journey | english | high |
| G14 | tradingqna | stop_or_fail | yes | yes | sip_or_mf_journey | english | medium |
| G15 | youtube | stop_or_fail | yes | yes | sip_or_mf_journey | hinglish | high |
| G16 **x** | appstore | returns | no | yes | sip_or_mf_journey | english | medium |
| G17 | play | returns | no | no | other | english | high |
| G18 | reddit | returns | yes | yes | sip_or_mf_journey | english | high |
| G19 **x** | tradingqna | returns | yes | no | other | english | high |
| G20 | youtube | returns | yes | yes | sip_or_mf_journey | english | high |

## Relevance disagreements

### G7 (play, sip_or_mf): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> mf does not have weekly stp option

### G8 (reddit, sip_or_mf): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> Might be easier to start another SIP in a liquid or ultra short duration fund and put a portion of your monthly investment there until you reach your target amount.
>
>
>       Then you can close to keep that as your emergency fund or withdraw it as a while and put it in an FD.

### G9 (tradingqna, sip_or_mf): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> [Feature request] Need option to select only mutual funds in Console
>
> Currently we see option to exclude the mutual funds in “Holdings” page which enables to select just stocks.
>
> Similarly I am looking for option to select just MF holdings for sector wise allocation and stocks they are holding.

### G10 (youtube, sip_or_mf): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> DSP Small Cap Fund - Direct Plan - Growth

### G12 (play, stop_or_fail): you no, engine yes as `sip_or_mf_journey` (high confidence)

> if you r using groww for only mf don't upgrade to dmat. otherwise u will redeem your money only thg Grow. that fund's app redeem money more faster than grow. grow takes 2 day more time

### G16 (appstore, returns): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> App barely has any features, xirr functionality works sometimes. Haven’t seen the app get any meaningful update in the last few years. Even filters to search for mutual funds are so so basic.

### G19 (tradingqna, returns): you yes, engine no as `other` (high confidence)

> Hi @thethinker, The CAGR returns that you see for mutual funds on Coin/Console or other platforms are shown after deduction of the expense ratio. This is because the NAV (Net Asset Value) of a mutual fund, which is used to calculate returns and CAGR, is declared after accounting for the expense ratio.
>
> So, any return, whether it’s the daily change or long-term CAGR like 1Y, 3Y, or 5Y, that you see based on NAVs is already net of the expense ratio.

