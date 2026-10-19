import {useCurrentFrame} from 'remotion';
import {COLORS, glow, textGlow} from '../theme';
import {Fade, MONO, SANS, Svg, clamp01} from './common';

const RED = '#ff4d6d';

// Nhà thiên văn kiểm tra lại dữ liệu, nghi ngờ thay vì phấn khích
export const Suspicion: React.FC = () => {
  const frame = useCurrentFrame();
  const waveY = (x: number) =>
    430 + Math.sin(x / 18 + frame / 6) * 55 * Math.sin(x / 140 + 1) + Math.sin(x / 5 + frame) * 8;
  let wave = '';
  for (let x = 320; x <= 1000; x += 6) wave += `${x === 320 ? 'M' : 'L'}${x} ${waveY(x)} `;

  const check = frame >= 240 ? 3 : frame >= 175 ? 2 : frame >= 100 ? 1 : 0;
  const lens = 380 + ((frame * 4) % 560);
  const flick = frame > 95 && frame < 105 ? 0.4 : 1;
  const strike = clamp01(frame, 30, 70);

  return (
    <Fade>
      <div style={{position: 'absolute', top: 50, width: '100%', textAlign: 'center', fontFamily: SANS, fontWeight: 700, fontSize: 52, letterSpacing: 8, color: '#8a8aa0'}}>
        EXCITEMENT
        <span style={{position: 'absolute', left: '50%', top: 36, height: 6, width: 420 * strike, marginLeft: -210, background: RED, boxShadow: `0 0 12px ${RED}`}} />
      </div>
      <div style={{position: 'absolute', top: 120, width: '100%', textAlign: 'center', fontFamily: SANS, fontWeight: 800, fontSize: 92, letterSpacing: 10, color: COLORS.text, textShadow: textGlow(COLORS.magenta), opacity: clamp01(frame, 95, 110) * flick}}>
        SUSPICION
      </div>

      <Svg>
        {/* màn hình */}
        <g fill="none" stroke={COLORS.cyan} strokeWidth="6" strokeLinecap="round" style={{filter: glow(COLORS.cyan, 0.7)}}>
          <rect x="280" y="290" width="760" height="420" rx="20" />
          <path d="M660 710 V780 M540 790 H780" />
          <path d={wave} stroke={COLORS.lime} strokeWidth="4" />
          <g stroke={COLORS.magenta} transform={`translate(${lens} 440)`}>
            <circle r="52" />
            <line x1="37" y1="37" x2="85" y2="85" strokeWidth="10" />
          </g>
        </g>
        <text x="310" y="345" fontFamily={MONO} fontSize="38" fill={COLORS.cyan}>
          {check > 0 ? `CHECK #${check}` : 'DATA'}
        </text>

        {/* nhà thiên văn */}
        <g fill="none" stroke={COLORS.magenta} strokeWidth="6" strokeLinecap="round" style={{filter: glow(COLORS.magenta, 0.7)}}>
          <circle cx="1420" cy="470" r="55" />
          <circle cx="1397" cy="462" r="5" fill={COLORS.magenta} />
          <path d="M1270 800 Q1280 610 1420 580 Q1560 610 1570 800" />
          <path d="M1300 700 Q1230 720 1130 690" />
        </g>

        {/* bong bóng suy nghĩ */}
        <g fill="none" stroke={COLORS.cyan} strokeWidth="4" style={{filter: glow(COLORS.cyan, 0.5)}} opacity={clamp01(frame, 20, 40)}>
          <circle cx="1475" cy="385" r="9" />
          <circle cx="1500" cy="345" r="15" />
          <ellipse cx="1560" cy="250" rx="130" ry="75" />
        </g>
        <text x="1560" y="285" textAnchor="middle" fontFamily={SANS} fontWeight="800" fontSize="100" fill={COLORS.text} opacity={clamp01(frame, 30, 45)} style={{filter: glow(COLORS.cyan, 0.5)}}>
          ?
        </text>
        {check >= 2 && (
          <text x="1560" y="560" textAnchor="middle" fontFamily={MONO} fontSize="36" fill={RED} style={{filter: glow(RED, 0.4)}}>
            AGAIN…
          </text>
        )}
      </Svg>
    </Fade>
  );
};
