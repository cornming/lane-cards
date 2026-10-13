// AI 對 AI 模擬：從 index.html 抽出遊戲引擎，跑多場對戰，確認不會卡死。
// 用法：node tests/sim.js [場數]
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const js = html.match(/<script>([\s\S]*)<\/script>/)[1];
const N = +(process.argv[2] || 400);
const harness = `
;(async()=>{
  const classes=Object.keys(CLASSES); const stats={games:0,turns:0,maxT:0,firstWin:0,stuck:0}; const wins={};
  for(let g=0;g<${N};g++){
    const a=classes[g%4], b=classes[Math.floor(g/4)%4];
    newGame(a,b);
    const sd=S.sides.P; for(const c of sd.hand) c.wait=Math.max(0,c.wait-1); draw('P');
    let guard=0;
    while(S.phase==='play'&&guard++<300){ await aiTurn('P'); if(S.phase!=='play') break; await endTurn('P'); }
    if(S.phase==='play'){stats.stuck++; continue;}
    stats.games++; stats.turns+=S.turn; stats.maxT=Math.max(stats.maxT,S.turn);
    if(S.winner==='P') stats.firstWin++;
    const w=S.winner==='P'?a:b; wins[w]=(wins[w]||0)+1;
  }
  console.log('對戰', stats.games, '場｜平均', (stats.turns/stats.games).toFixed(1), '回合｜最長', stats.maxT, '｜先手勝', stats.firstWin, '｜卡死', stats.stuck);
  console.log('各職業勝場', wins);
  if(stats.stuck>0){ console.error('有對戰沒有結束'); process.exit(1); }
})().catch(e=>{console.error(e); process.exit(1);});`;
eval(js + harness);
