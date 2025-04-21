import typescript from '@rollup/plugin-typescript';

export default {
  input: 'src/hello.ts',
  output: {
    file: 'dist/bundle.js',
    format: 'umd',
    name: 'SeaTest1',
  },
  plugins: [
    typescript({
      tsconfig: './tsconfig.json'
    }),
  ],
};