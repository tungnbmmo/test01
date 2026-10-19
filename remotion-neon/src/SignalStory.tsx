import {AbsoluteFill, Sequence} from 'remotion';
import {Background} from './Background';
import {Subtitles, Cue} from './Subtitles';
import {Telescope} from './scenes/Telescope';
import {Pattern} from './scenes/Pattern';
import {HourByHour} from './scenes/HourByHour';
import {Suspicion} from './scenes/Suspicion';
import {Wow} from './scenes/Wow';
import {ProveWrong} from './scenes/ProveWrong';

// [bắt đầu, độ dài] mỗi cảnh (frame @ 30fps)
const SCENES = [
  {from: 0, d: 180, C: Telescope},
  {from: 180, d: 240, C: Pattern},
  {from: 420, d: 150, C: HourByHour},
  {from: 570, d: 300, C: Suspicion},
  {from: 870, d: 300, C: Wow},
  {from: 1170, d: 240, C: ProveWrong},
];

export const STORY_DURATION = 1410;

const CUES: Cue[] = [
  {from: 15, to: 170, text: 'Tomorrow morning, a radio telescope picks up a signal.'},
  {from: 195, to: 305, text: 'It isn’t noise, and it isn’t a glitch.'},
  {from: 310, to: 415, text: 'It repeats in a pattern that nature cannot make.'},
  {from: 430, to: 490, text: 'What happens next?'},
  {from: 495, to: 565, text: 'Let’s go hour by hour.'},
  {from: 580, to: 660, text: 'The first reaction isn’t excitement.'},
  {from: 665, to: 720, text: 'It’s suspicion.'},
  {from: 725, to: 800, text: 'A young astronomer checks the data again.'},
  {from: 805, to: 865, text: 'Then again.'},
  {from: 880, to: 960, text: 'Scientists have been here before.'},
  {from: 965, to: 1075, text: 'In 1977, the famous “Wow!” signal lasted 72 seconds'},
  {from: 1080, to: 1165, text: 'and was never heard again.'},
  {from: 1180, to: 1290, text: 'So the team does what science demands:'},
  {from: 1295, to: 1405, text: 'they try to prove themselves wrong.'},
];

export const SignalStory: React.FC = () => (
  <AbsoluteFill>
    <Background />
    {SCENES.map(({from, d, C}) => (
      <Sequence key={from} from={from} durationInFrames={d}>
        <C />
      </Sequence>
    ))}
    <Subtitles cues={CUES} />
  </AbsoluteFill>
);
