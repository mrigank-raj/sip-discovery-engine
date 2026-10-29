# Golden set: relevance only

Stratified for coverage, not proportional to volume; 20 items, so every rate rests on very few items.

- Agreement: 55% (11/20)
- Engine said relevant and you agreed (precision): 40% (6/15)
- You said relevant and the engine agreed (recall): 100% (6/6)
- By source: appstore 50% (2/4); play 25% (1/4); reddit 75% (3/4); tradingqna 50% (2/4); youtube 75% (3/4)
- By prefilter group: stop_or_fail 60% (3/5); returns 70% (7/10); sip_or_mf 20% (1/5)

## Relevance, item by item

| # | source | group | you | engine | engine family | language | confidence |
|---|---|---|---|---|---|---|---|
| G1 **x** | appstore | returns | no | yes | sip_or_mf_journey | english | medium |
| G2 **x** | play | returns | no | yes | sip_or_mf_journey | english | high |
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
| G14 **x** | tradingqna | stop_or_fail | no | yes | sip_or_mf_journey | english | medium |
| G15 | youtube | stop_or_fail | yes | yes | sip_or_mf_journey | hinglish | high |
| G16 **x** | appstore | returns | no | yes | sip_or_mf_journey | english | medium |
| G17 | play | returns | no | no | other | english | high |
| G18 | reddit | returns | yes | yes | sip_or_mf_journey | english | high |
| G19 | tradingqna | returns | no | no | other | english | high |
| G20 | youtube | returns | yes | yes | sip_or_mf_journey | english | high |

## Relevance disagreements

### G1 (appstore, returns): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> INDmoney’s investment tracking needs significant improvement. It does not display XIRR for investments held for less than one year, making it difficult to accurately evaluate short-term investment performance.
>
> More importantly, there is no consolidated portfolio-level view showing metrics such as XIRR and total Gain/Loss across the entire portfolio, including both Stocks and Mutual Funds. Users should not have to analyze each investment category separately to understand their overall performance.
>
> A comprehensive portfolio dashboard with consolidated XIRR, absolute returns, total invested amount, current value, and overall Gain/Loss would make the app far more useful for tracking investments.

### G2 (play, returns): you no, engine yes as `sip_or_mf_journey` (high confidence)

> Your app shows me only historic XIRR returns of entire MF portfolio but not able to see my last 3M, 6M, 1Y, 3Y XIRR returns in MF . Kindly add this like other apps Zerodha, Groww.

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

### G14 (tradingqna, stop_or_fail): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> Does it give detailed  CG statement with for each quarter as mandated by tax forms?

### G16 (appstore, returns): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> App barely has any features, xirr functionality works sometimes. Haven’t seen the app get any meaningful update in the last few years. Even filters to search for mutual funds are so so basic.

