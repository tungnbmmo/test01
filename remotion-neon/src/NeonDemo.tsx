import {AbsoluteFill} from 'remotion';
import {Background} from './Background';
import {NeonShapes} from './NeonShapes';
import {AnimatedTitle} from './AnimatedTitle';
import {Subtitles, Cue} from './Subtitles';

export const DURATION = 240; // 8 giây @ 30fps

// Sửa phụ đề tại đây (đơn vị: frame)
const CUES: Cue[] = [
  {from: 30, to: 105, text: 'Đồ họa vector hoàn toàn bằng SVG'},
  {from: 110, to: 180, text: 'Nền tối, hiệu ứng neon glow'},
  {from: 185, to: 235, text: 'Tạo video bằng code với Remotion'},
];

export const NeonDemo: React.FC = () => (
  <AbsoluteFill>
    <Background />
    <NeonShapes />
    <AnimatedTitle text="NEON REMOTION" />
    <Subtitles cues={CUES} />
  </AbsoluteFill>
);
