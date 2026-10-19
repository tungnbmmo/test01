import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, glow} from './theme';

// Vòng tròn neon tự vẽ nét (stroke-dashoffset) + hình tam giác xoay
export const NeonShapes: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const circleLen = 2 * Math.PI * 200;
  const draw = interpolate(frame, [0, 60], [circleLen, 0], {extrapolateRight: 'clamp'});
  const pop = spring({frame: frame - 20, fps, config: {damping: 12}});
  const rot = frame * 1.2;
  const pulse = 0.75 + 0.25 * Math.sin(frame / 8);

  return (
    <svg width="100%" height="100%" viewBox="0 0 1920 1080" style={{position: 'absolute'}}>
      <g transform="translate(960 440)" style={{opacity: pulse}}>
        <circle
          r="200"
          fill="none"
          stroke={COLORS.cyan}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circleLen}
          strokeDashoffset={draw}
          style={{filter: glow(COLORS.cyan)}}
        />
        <g transform={`rotate(${rot}) scale(${pop})`} style={{filter: glow(COLORS.magenta)}}>
          <polygon
            points="0,-140 121,70 -121,70"
            fill="none"
            stroke={COLORS.magenta}
            strokeWidth="7"
            strokeLinejoin="round"
          />
        </g>
        <g transform={`rotate(${-rot * 1.5}) scale(${pop})`} style={{filter: glow(COLORS.lime)}}>
          <rect x="-60" y="-60" width="120" height="120" fill="none" stroke={COLORS.lime} strokeWidth="6" />
        </g>
      </g>
    </svg>
  );
};
