'use strict';

let timerId = null;

self.onmessage = function (event) {
    if (event.data === 'start') {
        if (timerId !== null) clearInterval(timerId);
        timerId = setInterval(() => {
            self.postMessage('tick');
        }, 25);
    } else if (event.data === 'stop' && timerId !== null) {
        clearInterval(timerId);
        timerId = null;
    }
};
