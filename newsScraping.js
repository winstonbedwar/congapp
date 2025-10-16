import nlp from 'compromise';
import axios from 'axios';
import Sentiment from 'sentiment';
//tomorrow: clean up sentiment analysis + add it to frontend (clean up as in make more accurate?? this is so cherry picked it's funny)
//what is async function? I feel like I'm missing the point and it's hitting me square in the
const blacklist = [
  'other purposes',
  'the category',
  'category',
  'purposes',
  'and',
  'of',
  'to',
  'in',
  'under',
  'for',
  'on',
  'by',
  'with',
  'a',
  'an',
  'amend',
  'title',
  'code',
  'united states code',
  'original resolution',
  'act'
];

const stopwords = new Set([
  'the', 'and', 'of', 'to', 'in', 'under', 'for', 'on', 'by', 'with', 'a', 'an', 'is', 'are'
]);

const pronouns = new Set([
  'its', 'his', 'her', 'their', 'our', 'your', 'my', 'their', 'mine', 'hers', 'ours', 'yours'
]);

function normalize(phrase) {
  let normalized = phrase.toLowerCase().trim();
  normalized = normalized.replace(/(\w+)'s\b/g, '$1');
  normalized = normalized.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "");
  return normalized;
}

function cleanPossessive(phrase) {
  const words = phrase.split(' ');
  const lastWord = words[words.length - 1];
  words[words.length - 1] = lastWord.replace(/’s$/i, '').replace(/'s$/i, '');
  return words.join(' ');
}

function removeBlacklistedWords(phrase) {
  const words = phrase.split(/\s+/);
  const filteredWords = words.filter(word => !blacklist.includes(word.toLowerCase()));
  return filteredWords.join(' ');
}

function isMeaningfulPhrase(phrase) {
  const normalized = normalize(phrase);

  if (blacklist.includes(normalized)) return false;

  const words = normalized.split(/\s+/);

  if (pronouns.has(words[0])) return false;

  if (words.length === 1 && stopwords.has(words[0])) return false;

  if (stopwords.has(words[0]) || stopwords.has(words[words.length - 1])) return false;

  if (normalized.length <= 2) return false;

  return true;
}

function extractNamedEntities(doc) {
  const people = doc.people().out('array');
  const orgs = doc.organizations().out('array');
  const places = doc.places().out('array');
  return [...people, ...orgs, ...places];
}

function extractProperNouns(doc) {
  const properNouns = doc.nouns().filter(n => n.has('#ProperNoun')).out('array');
  return properNouns;
}

function extractMeaningfulPhrases(text) {
  const doc = nlp(text);
  const namedEntities = extractNamedEntities(doc);
  const properNouns = extractProperNouns(doc);

  let combined = [...new Set([...namedEntities, ...properNouns])];

  combined = combined
    .map(cleanPossessive)
    .map(removeBlacklistedWords)
    .map(phrase => phrase.trim())
    .filter(phrase => phrase.length > 0);

  const filtered = combined.filter(isMeaningfulPhrase);

  if (filtered.length === 0) {
    return [text.trim()];
  }

  return filtered;
}

async function getArticles(query) {
  const url = `https://newsapi.org/v2/everything?q=${encodeURIComponent(query)}&sources=fox-news,cnn,reuters&apiKey=af38a4f95cc943dfbb33c1095461f40a`;

  try {
    const response = await axios.get(url);
    return response.data.articles.map(article => ({
      title: article.title,
      description: article.description,
      url: article.url,
      source: article.source.name,
    }));
  } catch (error) {
    console.error('Error fetching articles:', error);
    return [];
  }
}

const sentiment = new Sentiment();
let sumofAttitudeFox = 0; 
let numArticlesFox = 0;
let sumofAttitudeCNN = 0; 
let numArticlesCNN = 0;

//need Reuters or a more independent source as well???

// Example usage in an async context
(async () => {
  const billText = `Affirming the State of Palestine's right to exist.`;

  const meaningfulPhrases = extractMeaningfulPhrases(billText);
  console.log('Extracted meaningful phrases:', meaningfulPhrases);

  // Join phrases into a query string for the news API
  const query = meaningfulPhrases.join(' ');

  const articles = await getArticles(query);
  console.log('Fetched articles:', articles);

  const articlesWithSentiment = articles.map(article => {
    const text = `${article.title} ${article.description || ''}`;
    const analysis = sentiment.analyze(text);

     if(article.source == "Fox News"){
    sumofAttitudeFox = sumofAttitudeFox + analysis.comparative;
    numArticlesFox++;
  }

  if(article.source == "CNN"){
    sumofAttitudeCNN = sumofAttitudeCNN + analysis.comparative;
    numArticlesCNN++;
  }
    

    return {
      ...article,
      sentimentScore: analysis.score,
      sentimentComparative: analysis.comparative,
  };

  });

   console.log('Articles with sentiment:', articlesWithSentiment);
   console.log('Fox Sentiment:',sumofAttitudeFox/numArticlesFox);
   console.log('CNN sentiment',sumofAttitudeCNN/numArticlesCNN);

})();






//  import OpenAI from "openai"; <-- I'll get this to work tomorrow???

// const openai = new OpenAI({
//   apiKey: process.env.OPENAI_API_KEY,
// });

// async function extractKeyPhrasesFromText(text) {
//   const response = await openai.chat.completions.create({
//     model: "gpt-4o-mini",
//     messages: [
//       { role: "system", content: "You are a helpful assistant." },
//       { role: "user", content: `Extract key phrases from: ${text}` }
//     ],
//   });

//   return response.choices[0].message.content;
// }

// const exampleText = "To amend title 38, United States Code, to include eyeglass lens fittings...";
// extractKeyPhrasesFromText(exampleText).then(console.log);

// // Example usage:
// const billText = `To amend title 38, United States Code, to include eyeglass lens fittings 
// in the category of medical services authorized to be furnished to veterans 
// under the Veterans Community Care Program, and for other purposes.`;

// extractKeyPhrasesFromText(billText).then(phrases => {
//   console.log("Extracted key phrases:", phrases);
// });
// console.log("Extracted noun phrases:");
// console.log(result);









