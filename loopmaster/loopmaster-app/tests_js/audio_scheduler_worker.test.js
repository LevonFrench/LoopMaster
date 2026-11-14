const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function loadWorkerHarness() {
    const emitted = [];
    const cleared = [];
    const intervals = [];
    const context = {
        self: {
            postMessage(message) {
                emitted.push(message);
            },
        },
        setInterval(callback, delay) {
            const id = intervals.length + 1;
            intervals.push({ id, callback, delay });
            return id;
        },
        clearInterval(id) {
            cleared.push(id);
        },
    };
    const source = fs.readFileSync(
        path.resolve(__dirname, '..', 'static', 'audio-scheduler-worker.js'),
        'utf8',
    );
    vm.runInNewContext(source, context);
    return { context, emitted, cleared, intervals };
}

test('audio scheduler emits ticks and replaces or stops its active timer', () => {
    const harness = loadWorkerHarness();

    harness.context.self.onmessage({ data: 'start' });
    assert.equal(harness.intervals.length, 1);
    assert.equal(harness.intervals[0].delay, 25);
    harness.intervals[0].callback();
    assert.deepEqual(harness.emitted, ['tick']);

    harness.context.self.onmessage({ data: 'start' });
    assert.deepEqual(harness.cleared, [1]);
    assert.equal(harness.intervals.length, 2);

    harness.context.self.onmessage({ data: 'stop' });
    assert.deepEqual(harness.cleared, [1, 2]);
});
