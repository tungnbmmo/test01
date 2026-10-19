import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {COLORS} from './theme';

export const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const offset = (frame * 0.6) % 80;
  return (
    <AbsoluteFill style={{background: COLORS.bg}}>
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle at 50% 45%, rgba(120,40,220,0.28), transparent 60%)',
        }}
      />
      <svg width="100%" height="100%" viewBox="0 0 1920 1080" style={{opacity: 0.35}}>
        <defs>
          <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#fff" stopOpacity="0" />
            <stop offset="1" stopColor="#fff" stopOpacity="1" />
          </linearGradient>
          <mask id="m">
            <rect width="1920" height="1080" fill="url(#fade)" />
          </mask>
        </defs>
        <g mask="url(#m)" stroke={COLORS.magenta} strokeWidth="1.5">
          {Array.from({length: 14}).map((_, i) => (
            <line key={`h${i}`} x1="0" x2="1920" y1={560 + i * 40 + offset / 2} y2={560 + i * 40 + offset / 2} />
          ))}
          {Array.from({length: 25}).map((_, i) => (
            <line key={`v${i}`} x1={960 + (i - 12) * 40} y1="560" x2={960 + (i - 12) * 160} y2="1080" />
          ))}
        </g>
      </svg>
    </AbsoluteFill>
  );
};
