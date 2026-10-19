import {Composition} from 'remotion';
import {NeonDemo, DURATION} from './NeonDemo';
import {SignalStory, STORY_DURATION} from './SignalStory';

export const Root: React.FC = () => (
  <>
    <Composition id="NeonDemo" component={NeonDemo} durationInFrames={DURATION} fps={30} width={1920} height={1080} />
    <Composition id="SignalStory" component={SignalStory} durationInFrames={STORY_DURATION} fps={30} width={1920} height={1080} />
  </>
);
