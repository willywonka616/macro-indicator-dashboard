/* ------------------------------------------------------------------ *
 *  Hand-written interpretation text, keyed by country.
 *
 *  This is prose, written by a human, explaining what the picture means
 *  in Dalio's terms. It is NOT auto-generated from the numbers and there
 *  is no LLM call at build or runtime. The US text is carried over
 *  verbatim from the legacy dashboard.
 *
 *  Paragraphs are arrays of segments so we can keep the colour emphasis
 *  without dangerouslySetInnerHTML. A segment is { t } or { t, tone }
 *  where tone is one of: alarm | calm | mitig.
 *
 *  ⚠️ STALE-RISK FLAGS (see brief §6). These qualitative claims are
 *  pinned to live data and will silently contradict the chart if the
 *  data moves far enough:
 *   - "very high on long-term government debt risk" assumes headline
 *     govLT.z stays >= ~2. It comes from manual.json (Dalio model) and
 *     only changes when he republishes, so this is stable for now.
 *   - "short-term risk is low" assumes headline.shortTerm.level == "Low".
 *     If a future manual snapshot flips this, rewrite the second clause.
 *   - "point of no return" is Dalio's framing as of the March 2025
 *     snapshot; revisit if a later baseline softens it.
 *  If you change any of the above in manual.json, update this prose too.
 * ------------------------------------------------------------------ */

export const commentary = {
  US: {
    // Rendered under "What Dalio reads here".
    reads: [
      [
        { t: "The US scores " },
        { t: "very high on long-term government debt risk", tone: "alarm" },
        {
          t: ". Debt, debt service, and the sheer volume of new issuance and rollovers are the largest on record, and Dalio judges the situation to be nearing a point of no return, where a self-reinforcing debt spiral becomes hard to avoid. Yet ",
        },
        { t: "short-term risk is low", tone: "calm" },
        {
          t: ": inflation and growth are moderate, real rates sit in a workable range, and the private sector is healthy enough to tax if needed. That imminent gauge can flip almost overnight if demand for new debt weakens or holders start net-selling.",
        },
      ],
      [
        { t: "What holds the risk down is " },
        { t: "reserve-currency status", tone: "mitig" },
        {
          t: " — the dollar's dominance in trade, debt, equity markets, and central-bank reserves. Dalio calls this the single biggest mitigator, and warns US well-being hinges on keeping it.",
        },
      ],
    ],
    // Framing above the red-flags list.
    redFlagsIntro:
      "Things Dalio says we should expect not to see — and treat as serious warnings if we do:",
    // Rendered directly under the named panel (Panel.jsx's `longNote`), not
    // in the top "What Dalio reads here" box — a reader seeing two numbers
    // side by side (net/gross interest, debt/GDP vs debt/revenue) needs the
    // reason right there, not several screens down. Row labels themselves
    // carry the short version; this is the fuller explanation.
    panelNotes: {
      "Government debt": [
        [
          { t: "Net interest is the actual current situation", tone: "calm" },
          {
            t: " — cash genuinely leaving the government to holders of the debt, and the right measure of what servicing the debt costs today. ",
          },
          { t: "Gross interest is closer to a leading indicator.", tone: "alarm" },
          {
            t: " The difference is interest credited to government trust funds, paid not in cash but in additional bonds. That money was borrowed and spent years ago; what remains is a claim. When those bonds are redeemed, Treasury must raise real cash from the public — taxes, spending cuts, or new borrowing. So gross runs ahead of net, and the gap between them is an obligation building up before it appears as an outflow.",
          },
        ],
        [
          { t: "Debt/GDP measures the debt against the size of the whole economy", tone: "calm" },
          {
            t: " — the conventional comparison, and what makes countries comparable. ",
          },
          { t: "Debt/revenue measures it against what the government can actually collect", tone: "alarm" },
          {
            t: ", the money genuinely available to service it. The economy's output isn't the government's to spend; only its receipts are. So debt/GDP is the standard yardstick, while debt/revenue is closer to the burden actually carried — and it's the ratio Dalio's own equations are written in.",
          },
        ],
      ],
    },
  },
};

/* Dalio's own caveats — shown in the footer for every country. */
export const footerCaveats =
  "These gauges signal vulnerability, not timing, and they cover only the debt/financial slice of the picture. Political conflict, geopolitics, nature and technology all move the real outcome and are not captured here.";
