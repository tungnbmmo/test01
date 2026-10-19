import {useCurrentFrame} from 'remotion';
import {COLORS, glow, textGlow} from '../theme';
import {Fade, MONO, SANS, Svg, clamp01} from './common';

const X0 = 360;
const X1 = 1560;
const BASE = 680;

let curve = '';
for (let x = X0; x <= X1; x += 8) {
  const y = BASE - 330 * Math.exp(-Math.pow((x - 960) / 200, 2));
  curve += `${x === X0 ? 'M' : 'L'}${x} ${y} `;
}

// Tín hiệu "Wow!" 1977: 72 giây rồi biến mất
export const Wow: React.FC = () => {
  const frame = useCurrentFrame();
  const p = clamp01(frame, 110, 200);
  const seconds = Math.round(p * 72);
  const faded = clamp01(frame, 215, 250);
  const label = clamp01(frame, 190, 205);

  return (
    <Fade>
      <div style={{position: 'absolute', top: 60, width: '100%', textAlign: 'center', fontFamily: SANS, fontWeight: 800, fontSize: 110, letterSpacing: 10, color: COLORS.text, textShadow: textGlow(COLORS.cyan), opacity: clamp01(frame, 95, 110)}}>
        1977
      </div>
      <Svg>
        <rect x="300" y="220" width="1320" height="540" rx="24" fill="rgba(7,6,15,0.7)" stroke={COLORS.cyan} strokeWidth="3" style={{filter: glow(COLORS.cyan, 0.4)}} />
        <text x="330" y="262" fontFamily={MONO} fontSize="30" fill="#8a8aa0" opacity={1 - label}>ARCHIVE · BIG EAR RADIO TELESCOPE</text>
        <line x1={X0} x2={X1} y1={BASE} y2={BASE} stroke={COLORS.cyan} strokeWidth="2" opacity="0.4" />
        {/* đường quét */}
        {frame < 110 && (
          <line x1={X0 + ((frame * 12) % (X1 - X0))} x2={X0 + ((frame * 12) % (X1 - X0))} y1="300" y2={BASE} stroke={COLORS.cyan} opacity="0.4" strokeWidth="2" />
        )}

        <path d={curve} fill="none" stroke={COLORS.lime} strokeWidth="7" strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} opacity={1 - faded * 0.85} style={{filter: glow(COLORS.lime, 0.8)}} />
        <line x1={X0} x2={X1} y1={BASE} y2={BASE} stroke={COLORS.magenta} strokeWidth="5" strokeDasharray="14 14" opacity={faded} style={{filter: glow(COLORS.magenta, 0.5)}} />

        <text x="1590" y="345" textAnchor="end" fontFamily={MONO} fontSize="52" fill={COLORS.text} opacity={clamp01(frame, 105, 115)} style={{filter: glow(COLORS.cyan, 0.4)}}>
          {seconds} s
        </text>

        <g opacity={label}>
          <rect x="800" y="258" width="320" height="82" rx="10" fill="none" stroke={COLORS.magenta} strokeWidth="5" style={{filter: glow(COLORS.magenta, 0.6)}} />
          <text x="960" y="318" textAnchor="middle" fontFamily={MONO} fontWeight="700" fontSize="64" fill={COLORS.text}>6EQUJ5</text>
          <text x="1170" y="320" fontFamily="'Comic Sans MS', cursive" fontSize="84" fill={COLORS.magenta} transform="rotate(-8 1170 320)" style={{filter: glow(COLORS.magenta, 0.6)}}>
            Wow!
          </text>
        </g>

        <text x="960" y="860" textAnchor="middle" fontFamily={SANS} fontWeight="800" fontSize="64" letterSpacing="6" fill={COLORS.text} opacity={clamp01(frame, 235, 255)} style={{filter: glow(COLORS.magenta, 0.6)}}>
          NEVER HEARD AGAIN
        </text>
      </Svg>
    </Fade>
  );
};
