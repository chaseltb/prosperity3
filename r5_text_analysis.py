import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download VADER if not already installed
nltk.download('vader_lexicon')

# Initialize the Sentiment Analyzer
sia = SentimentIntensityAnalyzer()

# Sample texts (you can replace or expand this)
texts = {
    "Cactus Needle Spikes": "The Economic Express, the fastest steam train in our archipelago, went off track this morning. The incident occurred in a wide-open field and caused no material damage. However, getting the train back on track is expected to take significant effort and time. Investigators at the scene quickly identified the cause of the derailment: There is no doubt that the Cacti Needle Rail Spikes are to blame. What was once hailed as the greatest innovation of recent decades has turned out to be a small flaw with massive consequences. Experts now warn that the railway across the entire archipelago may need to be inspected inch by inch to ensure every CNRS is replaced with sturdy steel rail spikes.",
    "Quantum Coffee": "Will questionable side effects kill the Quantum Coffee hype? Quantum Coffee promised to be the energy booster of the future, and inhabitants were quick to jump on the high-tech hot brew, eager for next- level energy. Although users have reported sleepless nights and uncontrolled jitters for some time, doctors have now assessed the long- term health effects of Quantum Coffee. The preliminary report reveals dangerously high levels of 'Quantum Jitterwaves,' an newly discovered energy compound that overstimulates the nervous system. Symptoms include extreme restlessness, short- term memory glitches, and, a severe form of smelly coffee breath. Alarmed by the results, authorities are now debating an immediate ban on the once-hyped brew.",
    "Sauce": "Saloon Snacks Inc. makes a smooth move to acquire Saucy Sisters & Co. It's no secret that the hottest sauce in saloons across the West Archipelago right now is the famous Ranch Sauce from Saucy Sisters & Co. Saloon Snacks Inc. has been eyeing this ongoing success for some time, hinting at a potential takeover. However, they've struggled to entice the Saucy Sisters with a deal, as the key sticking point in negotiations has been the name. Both 'Saucy Sister Saloon Snacks Inc.' and 'Saloon Snack Saucy Sisters & Co.' were rejected right away. But now, Saloon Snacks Inc. has made a smooth move with a new proposal: 'Saucy Snacks & Co.' - a name that seems to have sealed the deal. Going forward, Saucy Sisters & Co. will sell all their stock at a fixed price to Saloon Snacks Inc. A representative hinted at a special edition bottle of Ranch Sauce to celebrate the occasion.",
    "Solar Panels": "Taxes on solar panels increase overnight. Harvesting the power of the sun has become fully integrated into our daily lives, with solar panels on almost every single house. But that doesn't mean you can keep all that energy to yourself, says Benny the Bull. Unpopular as it may seem, the proposed 8.4% tax increase on solar panels will take effect tomorrow morning. This new tax law triples the cost of owning solar panels and applies to every single panel you own. The legislation casts a dark shadow over what was otherwise a bright and promising development.",
    "Moonshine": "Next Moonshine Space Expedition on the way. The first-ever Moonshine Space Expedition, carrying several hundred bottles of Moonshine, returned last week. CosmicClean CEO Mr. Gleam was quick to declare the mission a success, but scientists at the Lunar Observatory remain unconvinced. Cleaning the surface of the moon with Moonshine didn't actually make the moon shine brighter, said a spokesperson for the Lunar Observatory. Mr. Gleam made it no secret that he's already planning his next launch. When asked for a reaction, he repeated his mission statement with characteristic enthusiasm: The moon will be brighter than ever, that's a given. I have high hopes this next expedition will blow everyone's mind. To the moon!",
    "Haystacks": "Whispers of needles in haystacks to ignite Hayfever frenzy? Haystacks have always been popular amongst our population. But the hot weather makes dry grass omnipresent and making it freely available on virtually every street corner. The value of Haystacks falling fast, with consumers complaining that it lacks innovation. With the abyss of oblivion in sight, no one really believed in a revival. No one, except a decentralized community of amateur researchers with computers in sheds, known as Sheddit. Some of the community members found some rare pearl needles hidden in a large part of this years Haystack production. If this turns out to be true, it will definitely be a game changer for DryGrass & Sons and their single product portfolio. Some say that the discovery of this first needle could be the start of a nation wide Hayfever.",
    "Red Flags": "Sandstorm blows Red Flag Reserve to smithereens. Red flags everywhere! A massive sandstorm recently hit the Red Flag Reserve, sending red flags flying in every direction. Most of the flags were broken by the storm, but Bulls still went wild and seemed aimless, charging into walls and each other causing chaos across the region. The once-thriving base of operations for the Red Flag Trading Company, known for its highly sought- after commodities, is now left in ruins. In the midst of the chaos, a few determined bulls at the Red Flag Reserve managed to save a handful of flags, though not without incident. The Red Flag Reserve has promised that the missing red flags will be reprinted during the coming months, although some predict it might take longer than expected.",
    "Shirts": "The whole world will be dressed in Black and Yellow. As yearly tradition, fashion experts and trendwatchers are speculating on the next big trend. The Dalton Brothers entered the conversation, confidently declaring that black and yellow striped shirts will dominate store racks next season. A bold claim, especially from new faces in the fashion scene, but they seem pretty confident about their prediction. When asked where they based their prediction on, they were quick to point to their new Spring/Summer collection of black and yellow striped shirts, available in their online shop, even adding a HYPEDSTRIPED discount code.",
    "VR Headsets": "Popularity of VR Quick Draw even higher than experts expected, as quarterly reports show. There's no way around it: VR Quick Draw has the entire archipelago engaged in harmless duels. Rumor has it some are even using the game to settle serious disputes. Baita, the company behind the popular game and the VR Monocle device it's played on, just released their quarterly results. Monthly Active Players (MAPs) have skyrocketed from 800K last quarter to an astonishing 4.6 million this quarter. Meanwhile, the Average Time Spent in Quick Draw Duels has hit an all-time high of 18 hours and 32 minutes. These staggering numbers leave one wondering: how does anyone get enough sleep, let alone find time to get any work done?"
}

# Your manual scores (scale: -1 to 1, matching VADER's compound score range)
manual_scores = {
    "Cactus Needle Spikes": -0.9,
    "Quantum Coffee": -0.6,
    "Sauce": 0.3,
    "Solar Panels": -0.6,
    "Moonshine": 0.0,
    "Haystacks": 0.0,
    "Red Flags": -0.6,
    "Shirts": 0.6,
    "VR Headsets": 0.9
}

# Weight factors
vader_weight = 0.4
manual_weight = 0.6

# Analyze and combine scores
for label, text in texts.items():
    vader_score = sia.polarity_scores(text)['compound']
    manual_score = manual_scores.get(label, 0)
    combined_score = vader_score * vader_weight + manual_score * manual_weight

    sentiment = (
        "Very Positive" if combined_score > 0.4 else
        "Slightly Positive" if 0.1 < combined_score < 0.4 else
        "Slightly Negative" if -0.4 < combined_score < -0.1 else
        "Very Negative" if combined_score < -0.4 else
        "Neutral"
    )

    print(f"{label}:\n"
          f"VADER: {vader_score:.2f} Manual: {manual_score:.2f}\n"
          f"Combined Score: {combined_score:.2f} = {sentiment}\n")
