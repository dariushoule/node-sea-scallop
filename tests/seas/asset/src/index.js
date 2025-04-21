const { getAsset } = require('node:sea');
console.log('payload/abc.txt -> ', getAsset('payload/abc.txt', 'utf8'));
console.log('payload/def.txt -> ', getAsset('payload/def.txt', 'utf8'));