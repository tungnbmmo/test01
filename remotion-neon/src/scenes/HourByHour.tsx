import {Sequence, useCurrentFrame} from 'remotion';
import {AnimatedTitle} from '../AnimatedTitle';
import {COLORS, glow, textGlow} from '../theme';
import {Fade, SANS, Svg, clamp01} from './common';

export const HourByHour: React.FC = () => {
  const frame = useCurrentFrame();
  const minute = frame * 6;
  const hour = frame * 0.5;
  return (
    <Fade>
      <div style={{position: 'absolute', top: 80, width: '100%', textAlign: 'center', fontFamily: SANS, fontWeight: 700, fontSize: 64, letterSpacing: 6, color: COLORS.text, textShadow: textGlow(COLORS.magenta), opacity: clamp01(frame, 0, 15)}}>
        WHAT HAPPENS NEXT?
      </div>
      <Svg>
        <g transform="translate(960 440)" fill="none" stroke={COLORS.cyan} strokeLinecap="round" style={{filter: glow(COLORS.cyan, 0.8)}}>
          <circle r="190" strokeWidth="8" strokeDasharray={2 * Math.PI * 190} strokeDashoffset={(1 - clamp01(frame, 0, 40)) * 2 * Math.PI * 190} />
          {Array.from({length: 12}).map((_, i) => (
            <line key={i} y1="-160" y2="-175" strokeWidth="6" transform={`rotate(${i * 30})`} opacity={clamp01(frame, 20 + i * 2, 30 + i * 2)} />
          ))}
          <line y2="-100" strokeWidth="10" stroke={COLORS.magenta} transform={`rotate(${hour})`} />
          <line y2="-150" strokeWidth="6" stroke={COLORS.lime} transform={`rotate(${minute})`} />
          <circle r="12" fill={COLORS.cyan} />
        </g>
      </Svg>
      <Sequence from={70}>
        <AnimatedTitle text="HOUR BY HOUR" top={700} size={130} color={COLORS.magenta} />
      </Sequence>
    </Fade>
  );
};
