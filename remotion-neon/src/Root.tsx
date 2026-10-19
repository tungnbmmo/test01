import {Composition} from 'remotion';
import {NeonDemo, DURATION} from './NeonDemo';

export const Root: React.FC = () => (
  <Composition
    id="NeonDemo"
    component={NeonDemo}
    durationInFrames={DURATION}
    fps={30}
    width={1920}
    height={1080}
  />
);
