/**
 * EduGuide Text-to-Speech Service
 * Simple wrapper for the Web Speech API.
 */

window.EduGuideTTS = {
    enabled: true,
    voice: null,

    init() {
        if (!('speechSynthesis' in window)) {
            console.warn("TTS not supported in this browser.");
            this.enabled = false;
            return;
        }

        // Try to find a Swedish voice
        const setVoice = () => {
            const voices = window.speechSynthesis.getVoices();
            this.voice = voices.find(v => v.lang.startsWith('sv')) || voices[0];
        };

        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = setVoice;
        }
        setVoice();
    },

    speak(text) {
        if (!this.enabled) return;

        // Cancel any current speech
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        if (this.voice) {
            utterance.voice = this.voice;
        }
        // Slightly slower and friendlier pitch
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        utterance.lang = 'sv-SE';

        window.speechSynthesis.speak(utterance);
    }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    window.EduGuideTTS.init();
});
