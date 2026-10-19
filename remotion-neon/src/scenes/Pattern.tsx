import {useCurrentFrame, random} from 'remotion';
import {COLORS, glow} from '../theme';
import {Fade, MONO, Svg, clamp01} from './common';

const X0 = 520;
const X1 = 1500;
const ROWS = [250, 500, 750];
const RED = '#ff4d6d';

const noisePath = (seed: number) => {
  let d = '';
  for (let x = 0; x <= X1 - X0; x += 8) {
    const y = ROWS[0] + (random(`n${seed}-${x}`) - 0.5) * 120;
    d += `${x === 0 ? 'M' : 'L'}${X0 + x} ${y} `;
  }
  return d;
};

const cy2 = ROWS[1];
const glitchPath = `M${X0} ${cy2} H${X0 + 400} L${X0 + 410} ${cy2 - 90} L${X0 + 422} ${cy2 + 90} L${X0 + 432} ${cy2} H${X1}`;

const PERIOD = (X1 - X0) / 4;
const cy3 = ROWS[2];
const patternPath =
  `M${X0} ${cy3} ` +
  [0, 1, 2, 3]
    .map((k) => {
      const s = X0 + k * PERIOD;
      return `H${s + 20} V${cy3 - 80} H${s + 55} V${cy3} H${s + 90} V${cy3 - 80} H${s + 165} V${cy3}`;
    })
    .join(' ') +
  ` H${X1}`;

const Cross: React.FC<{cx: number; cy: number; p: number}> = ({cx, cy, p}) => (
  <g stroke={RED} strokeWidth="9" strokeLinecap="round" style={{filter: glow(RED, 0.6)}}>
    <line x1={cx - 28} y1={cy - 28} x2={cx - 28 + 56 * Math.min(p * 2, 1)} y2={cy - 28 + 56 * Math.min(p * 2, 1)} />
    <line x1={cx + 28} y1={cy - 28} x2={cx + 28 - 56 * Math.max(p * 2 - 1, 0)} y2={cy - 28 + 56 * Math.max(p * 2 - 1, 0)} />
  </g>
);

// Nhiễu, nhiễu một lần, và một chuỗi xung lặp lại
export const Pattern: React.FC = () => {
  const frame = useCurrentFrame();
  const draw = (p: number) => ({pathLength: 1, strokeDasharray: 1, strokeDashoffset: 1 - p});
  const label = (y: number, text: string, color: string) => (
    <text x="290" y={y + 12} fontFamily={MONO} fontSize="38" fill={color} style={{filter: glow(color, 0.4)}}>
      {text}
    </text>
  );

  return (
    <Fade>
      <Svg>
        <rect x="240" y="110" width="1440" height="770" rx="24" fill="rgba(7,6,15,0.7)" stroke={COLORS.cyan} strokeWidth="3" style={{filter: glow(COLORS.cyan, 0.4)}} />
        {ROWS.map((y) => (
          <line key={y} x1="260" x2="1660" y1={y} y2={y} stroke={COLORS.cyan} strokeWidth="1" opacity="0.2" />
        ))}

        {label(ROWS[0], 'NOISE', COLORS.cyan)}
        <path d={noisePath(Math.floor(frame / 2))} fill="none" stroke={COLORS.cyan} strokeWidth="4" opacity={frame > 70 ? 0.35 : 1} style={{filter: glow(COLORS.cyan, 0.5)}} />
        <Cross cx={1590} cy={ROWS[0]} p={clamp01(frame, 70, 90)} />

        {label(ROWS[1], 'GLITCH', COLORS.cyan)}
        <path d={glitchPath} fill="none" stroke={COLORS.cyan} strokeWidth="4" opacity={frame > 130 ? 0.35 : 1} {...draw(clamp01(frame, 40, 110))} style={{filter: glow(COLORS.cyan, 0.5)}} />
        <Cross cx={1590} cy={ROWS[1]} p={clamp01(frame, 130, 150)} />

        {label(ROWS[2], 'PATTERN', COLORS.magenta)}
        {[1, 2, 3].map((k) => (
          <line key={k} x1={X0 + k * PERIOD} x2={X0 + k * PERIOD} y1={cy3 - 110} y2={cy3 + 40} stroke={COLORS.lime} strokeDasharray="6 8" strokeWidth="2" opacity={clamp01(frame, 120 + k * 20, 130 + k * 20) * 0.7} />
        ))}
        <path d={patternPath} fill="none" stroke={COLORS.magenta} strokeWidth="6" strokeLinejoin="round" {...draw(clamp01(frame, 125, 205))} style={{filter: glow(COLORS.magenta)}} />
        <g opacity={clamp01(frame, 205, 215)} stroke={COLORS.lime} strokeWidth="9" fill="none" strokeLinecap="round" style={{filter: glow(COLORS.lime, 0.7)}}>
          <path d="M1560 750 L1585 778 L1625 718" />
        </g>
      </Svg>
    </Fade>
  );
};
