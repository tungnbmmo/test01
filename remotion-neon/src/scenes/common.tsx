import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

export const MONO = 'Consolas, "Courier New", monospace';
export const SANS = 'Segoe UI, Arial, sans-serif';

export const Fade: React.FC<{children: React.ReactNode}> = ({children}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const opacity = interpolate(frame, [0, 10, durationInFrames - 10, durationInFrames], [0, 1, 1, 0]);
  return <AbsoluteFill style={{opacity}}>{children}</AbsoluteFill>;
};

export const Svg: React.FC<{children: React.ReactNode}> = ({children}) => (
  <svg viewBox="0 0 1920 1080" width="100%" height="100%" style={{position: 'absolute'}}>
    {children}
  </svg>
);

export const clamp01 = (frame: number, from: number, to: number) =>
  interpolate(frame, [from, to], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
