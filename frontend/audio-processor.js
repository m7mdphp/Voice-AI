/**
 * Tiryaq PCM 16000 Processor
 * Specialized AudioWorklet for low-latency SaaS voice AI.
 */
class PCMProcessor extends AudioWorkletProcessor {
    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (input && input.length > 0) {
            const channelData = input[0];
            const pcmData = new Int16Array(channelData.length);

            for (let i = 0; i < channelData.length; i++) {
                // Gain boost (1.5x) + Int16 scaling
                let sample = channelData[i] * 1.5;
                // Clipping protection
                pcmData[i] = Math.max(-32768, Math.min(32767, sample * 32768));
            }

            this.port.postMessage(pcmData.buffer, [pcmData.buffer]);
        }
        return true;
    }
}

registerProcessor('pcm-processor', PCMProcessor);
