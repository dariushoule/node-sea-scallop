const v8 = require('v8');
let state;

function __main() {
    state = 1;
    console.log("snapsnap");
}

__main();
v8.startupSnapshot.setDeserializeMainFunction(__main);