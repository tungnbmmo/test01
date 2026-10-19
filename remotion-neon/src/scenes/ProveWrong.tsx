import {Sequence, useCurrentFrame} from 'remotion';
import {AnimatedTitle} from '../AnimatedTitle';
import {COLORS, glow, textGlow} from '../theme';
import {Fade, MONO, SANS, Svg, clamp01} from './common';

const ITEMS = ['INSTRUMENT FAULT?', 'RADIO INTERFERENCE?', 'SATELLITE OR AIRCRAFT?', 'DATA PROCESSING ERROR?'];

// Nhóm nghiên cứu cố gắng bác bỏ chính mình
export const ProveWrong: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Fade>
      {frame < 100 && (
        <div style={{position: 'absolute', top: 100, width: '100%', textAlign: 'center', fontFamily: SANS, fontWeight: 800, fontSize: 90, letterSpacing: 8, color: COLORS.text, textShadow: textGlow(COLORS.cyan), opacity: clamp01(frame, 0, 15) * (1 - clamp01(frame, 90, 100))}}>
          WHAT SCIENCE DEMANDS
        </div>
      )}
      <Sequence from={100}>
        <AnimatedTitle text="PROVE YOURSELF WRONG" top={100} size={90} color={COLORS.magenta} />
      </Sequence>
      <Svg>
        {ITEMS.map((text, i) => {
          const start = 130 + i * 25;
          const o = clamp01(frame, start, start + 12);
          const y = 360 + i * 130;
          return (
            <g key={text} opacity={o} transform={`translate(0 ${(1 - o) * 30})`}>
              <rect x="500" y={y} width="76" height="76" rx="10" fill="none" stroke={COLORS.cyan} strokeWidth="5" style={{filter: glow(COLORS.cyan, 0.6)}} />
              <circle cx="538" cy={y + 38} r="22" fill="none" stroke={COLORS.lime} strokeWidth="5" strokeLinecap="round" strokeDasharray="35 104" transform={`rotate(${(frame - start) * 8} 538 ${y + 38})`} style={{filter: glow(COLORS.lime, 0.5)}} />
              <text x="620" y={y + 56} fontFamily={MONO} fontSize="54" fill={COLORS.text} style={{filter: glow(COLORS.cyan, 0.3)}}>
                {text}
              </text>
            </g>
          );
        })}
      </Svg>
    </Fade>
  );
};
