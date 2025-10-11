import Cerebras from '@cerebras/cerebras_cloud_sdk';

const client = new Cerebras({
  apiKey: process.env['csk-yc3nryechcj9hp2etk44yffvwk6eetc4863eee3924n62fkw'], // This is the default and can be omitted
});

async function main() {
  const chatCompletion = await client.chat.completions.create({
    messages: [{ role: 'user', content: 'Summarize the us consittuion in 100 words' }],
    model: 'llama3.1-8b',
  });

  console.log(chatCompletion?.choices[0]?.message);
}

main();