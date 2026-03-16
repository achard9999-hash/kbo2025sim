import React, { useEffect, useState } from "react";
import { Streamlit } from "streamlit-component-lib";
import { motion } from "framer-motion";
import fieldImage from "../../image/야구장시뮬.png";
import mainBg from "../../image/메인화면.png";
import logoHanwha from "../../image/한화.png";
import logoKIA from "../../image/KIA.png";
import logoKT from "../../image/KT.png";
import logoSSG from "../../image/SSG.png";
import logoNC from "../../image/NC.png";
import logoSamsung from "../../image/삼성.png";
import logoDoosan from "../../image/두산.png";
import logoLotte from "../../image/롯데.png";
import logoLG from "../../image/LG.png";
import logoKiwoom from "../../image/키움.png";

function emitAction(type, payload = {}) {
  Streamlit.setComponentValue({
    type,
    payload,
    nonce: Date.now(),
  });
}

function useAutoHeight(deps) {
  useEffect(() => {
    const t = window.setTimeout(() => {
      Streamlit.setFrameHeight(document.documentElement.scrollHeight);
    }, 100);
    return () => window.clearTimeout(t);
  }, deps);
}

function fmtText(v, fallback = "-") {
  if (v === null || v === undefined || v === "") return fallback;
  return String(v);
}

function Chip({ children }) {
  return <span className="ss-chip">{children}</span>;
}

function Card({ title, children, className = "" }) {
  return (
    <div className={`ss-card ${className}`}>
      <div className="ss-card-title">{title}</div>
      {children}
    </div>
  );
}

const TEAM_LOGOS = {
  한화: logoHanwha,
  KIA: logoKIA,
  KT: logoKT,
  SSG: logoSSG,
  NC: logoNC,
  삼성: logoSamsung,
  두산: logoDoosan,
  롯데: logoLotte,
  LG: logoLG,
  키움: logoKiwoom,
};

function TeamLogo({ team, size = 52 }) {
  const src = TEAM_LOGOS[team];
  if (!src) return <div className="ss-team-logo-fallback">{team}</div>;
  return <img src={src} alt={team} className="ss-team-logo" style={{ width: size, height: size }} />;
}

function InfoRow({ label, value }) {
  return (
    <div className="ss-info-row">
      <div className="ss-info-label">{label}</div>
      <div className="ss-info-value">{value}</div>
    </div>
  );
}

function TeamLine({ side, name, score, active }) {
  return (
    <div className={`ss-team-panel ${active ? "active" : ""}`}>
      <div className="ss-team-side">{side}</div>
      <div className="ss-team-name">{name}</div>
      <div className="ss-team-score">{score}</div>
    </div>
  );
}

function BaseDiamond({ active, label }) {
  return (
    <div className="ss-base-wrap">
      <div className={`ss-base ${active ? "active" : ""}`} />
      <div className="ss-base-label">{label}</div>
    </div>
  );
}

function LogFeed({ lines }) {
  if (!lines?.length) {
    return <div className="ss-empty">로그가 아직 없습니다.</div>;
  }

  return (
    <div className="ss-log-list">
      {lines.map((line, idx) => (
        <div key={`${idx}-${line}`} className="ss-log-item">
          {line}
        </div>
      ))}
    </div>
  );
}

function NoLiveGame({ selectedGame }) {
  return (
    <div className="ss-shell">
      <Card title="실시간 경기">
        <div className="ss-empty-block">
          <div className="ss-empty-title">아직 시작한 한화 경기가 없습니다.</div>
          <div className="ss-empty-sub">
            {selectedGame?.away && selectedGame?.home
              ? `${selectedGame.away} vs ${selectedGame.home}`
              : "오늘 한화 경기 정보 대기 중"}
          </div>
          <button className="ss-primary-btn" onClick={() => emitAction("start_or_resume")}>
            경기 시작 / 이어서 진행
          </button>
        </div>
      </Card>
    </div>
  );
}

function HomeHub({ summary, screens, onNavigate }) {
  const latest = summary?.latest_result_text || "-";
  const menus = [
    { id: "schedule", title: "오늘 일정", sub: "오늘 경기와 한화 진행", tone: "blue" },
    { id: "live", title: "실시간 경기", sub: "야구장 화면으로 시뮬", tone: "red" },
    { id: "lineup", title: "한화 라인업", sub: "선발/벤치 구성", tone: "gray" },
    { id: "trade", title: "트레이드", sub: "전력 강화", tone: "gold" },
    { id: "standings", title: "순위", sub: "리그 테이블", tone: "navy" },
    { id: "leaders", title: "리더보드", sub: "타자/투수 TOP", tone: "green" },
  ];

  return (
    <div className="ss-home">
        <div className="ss-home-bg">
          <img src={mainBg} alt="메인화면" className="ss-home-bg-img" loading="lazy" />
        <div className="ss-home-bg-overlay" />
      </div>

      <motion.div
        className="ss-home-top"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.28 }}
      >
        <div className="ss-home-title">효진부터 시작되는 한화의 KS 우승!</div>
        <div className="ss-home-sub">야구부스토리 감성 · 한화 수동 운영 + 자동 시뮬 + 리더보드</div>
        <div className="ss-home-badges">
          <span className="ss-home-badge">현재 날짜 · {fmtText(summary?.current_date)}</span>
          <span className="ss-home-badge">한화 순위 · {fmtText(summary?.hanwha_rank_text)}</span>
          <span className="ss-home-badge">완료 경기 · {fmtText(summary?.completed_game_count, "0")}</span>
          <span className="ss-home-badge ss-home-badge-strong">최근 결과 · {latest}</span>
        </div>
      </motion.div>

      <div className="ss-home-grid">
        {menus.map((m, idx) => (
          <motion.button
            key={m.id}
            className={`ss-home-card tone-${m.tone}`}
            onClick={() => onNavigate(m.id)}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 * idx, duration: 0.25 }}
            whileHover={{ y: -3, scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            type="button"
          >
            <div className="ss-home-card-title">{m.title}</div>
            <div className="ss-home-card-sub">{m.sub}</div>
          </motion.button>
        ))}
      </div>

      <div className="ss-home-footer">
        <div className="ss-home-footer-note">메뉴를 클릭하면 해당 화면으로 전환됩니다.</div>
      </div>
    </div>
  );
}

function ScreenHeader({ title, onBack }) {
  return (
    <div className="ss-screen-header">
      <button className="ss-back-btn" onClick={onBack} type="button">← 메인</button>
      <div className="ss-screen-title">{title}</div>
    </div>
  );
}

function SimpleTable({ rows }) {
  if (!rows?.length) return <div className="ss-empty">표시할 데이터가 없습니다.</div>;
  const columns = Object.keys(rows[0] || {});
  return (
    <div className="ss-table-wrap">
      <div className="ss-table">
        <div className="ss-table-head">
          {columns.map((c) => <div key={`h-${c}`} className="ss-table-cell head">{c}</div>)}
        </div>
        {rows.map((r, i) => (
          <div key={`r-${i}`} className="ss-table-row">
            {columns.map((c) => <div key={`c-${i}-${c}`} className="ss-table-cell">{fmtText(r[c], "")}</div>)}
          </div>
        ))}
      </div>
    </div>
  );
}

function TradeScreen({ trade, onBack }) {
  const opponents = trade?.opponents || [];
  const markets = trade?.markets || {};
  const offerPool = trade?.offer_pool || [];
  const last = trade?.last_result || null;

  const [opp, setOpp] = useState(opponents[0] || "");
  const [target, setTarget] = useState("");
  const [offered, setOffered] = useState([]);

  useEffect(() => {
    const list = markets?.[opp] || [];
    setTarget(list[0]?.name || "");
    setOffered([]);
  }, [opp]);

  const marketList = markets?.[opp] || [];

  return (
    <div className="ss-shell">
      <ScreenHeader title="트레이드" onBack={onBack} />

      {last?.message ? (
        <div className={`ss-trade-result ${last.ok ? "ok" : "bad"}`}>
          {last.ok ? "성공" : "실패"} · {last.message}
        </div>
      ) : null}

      <div className="ss-two-col">
        <Card title="트레이드 제안">
          <div className="ss-form-block">
            <div className="ss-form-label">상대 팀</div>
            <select className="ss-select" value={opp} onChange={(e) => setOpp(e.target.value)}>
              {opponents.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div className="ss-form-block">
            <div className="ss-form-label">영입 대상</div>
            <select className="ss-select" value={target} onChange={(e) => setTarget(e.target.value)}>
              {(marketList || []).map((p) => (
                <option key={`${p.name}-${p.pos}`} value={p.name}>
                  {p.pos} / {p.name} (OPS {Number(p.ops || 0).toFixed(3)}, wRAA {Number(p.wraa || 0).toFixed(1)})
                </option>
              ))}
            </select>
          </div>

          <div className="ss-form-block">
            <div className="ss-form-label">제안 선수(한화 벤치)</div>
            <div className="ss-offer-grid">
              {offerPool.map((p) => {
                const checked = offered.includes(p.name);
                return (
                  <label key={p.name} className={`ss-offer-chip ${checked ? "on" : ""}`}>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        const on = e.target.checked;
                        setOffered((prev) => on ? [...prev, p.name] : prev.filter((x) => x !== p.name));
                      }}
                    />
                    <span>{p.pos} / {p.name}</span>
                  </label>
                );
              })}
            </div>
          </div>

          <button
            className="ss-primary-btn"
            onClick={() => emitAction("execute_trade", { opponent_team: opp, target_name: target, offered_names: offered })}
            disabled={!opp || !target || offered.length === 0}
            type="button"
          >
            트레이드 제안
          </button>
        </Card>

        <Card title="상대 팀 마켓 미리보기">
          <div className="ss-trade-market">
            {(marketList || []).slice(0, 40).map((p) => (
              <div key={`m-${p.name}-${p.pos}`} className="ss-trade-row">
                <div className="ss-trade-name">{p.pos} / {p.name}</div>
                <div className="ss-trade-meta">OPS {Number(p.ops || 0).toFixed(3)} · wRAA {Number(p.wraa || 0).toFixed(1)}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

export default function HanwhaDashboard(props) {
  const appPayload = props.args?.appPayload || {};
  const live = appPayload.live_game || {};
  const game = live.game_state || null;
  const manager = live.manager_actions || {};
  const summary = appPayload.season_summary || {};
  const screens = appPayload.screens || {};
  const lastError = screens?.last_error;

  const [screen, setScreen] = useState("home");

  const [phName, setPhName] = useState("");
  const [prName, setPrName] = useState("");
  const [prBase, setPrBase] = useState(1);
  const [manualRole, setManualRole] = useState("");

  useEffect(() => {
    if (manager.pr_base_choices?.length) {
      setPrBase(manager.pr_base_choices[0]);
    } else {
      setPrBase(1);
    }
  }, [manager.pr_base_choices]);

  const bases = game?.bases || [];
  const base1 = !!bases[0];
  const base2 = !!bases[1];
  const base3 = !!bases[2];

  const lineAway = game?.line_score?.away_display || Array(9).fill("");
  const lineHome = game?.line_score?.home_display || Array(9).fill("");

  const currentBatter = game?.current_batter || {};
  const currentPitcher = game?.current_pitcher || {};

  const activeSide = game?.half === "top" ? "away" : "home";
  const hasLiveGame = !!live.has_live_game && !!game;

  const awayState = game?.away_state;
  const homeState = game?.home_state;
  const totals = game?.totals || {};
  const awayTotals = totals.away || {};
  const homeTotals = totals.home || {};

  const maxInnings = Math.max(
    11,
    (game?.line_score?.away?.length || 0),
    (game?.line_score?.home?.length || 0),
  );

  useAutoHeight([
    // 화면 종류가 바뀔 때만 전체 높이를 다시 계산하도록 제한
    screen,
  ]);

  if (screen === "home") {
    return (
      <HomeHub
        summary={summary}
        screens={screens}
        onNavigate={(id) => setScreen(id)}
      />
    );
  }

  if (screen === "schedule") {
    const rows = screens?.today_schedule?.rows || [];
    const hgRows = screens?.hanwha_games?.rows || [];
    const selectedIdx = Number(screens?.hanwha_games?.selected_idx || 0);
    return (
      <div className="ss-shell">
        <ScreenHeader title="오늘 일정" onBack={() => setScreen("home")} />
        {lastError ? <div className="ss-error-banner">오류 · {lastError}</div> : null}
        <Card title={`오늘 전체 일정 (${fmtText(screens?.today_schedule?.date)})`}>
          <SimpleTable rows={rows} />
        </Card>
        <Card title="오늘 한화 경기">
          {hgRows.length ? (
            <div className="ss-form-block">
              <div className="ss-form-label">진행할 한화 경기 선택</div>
              <select
                className="ss-select"
                value={selectedIdx}
                onChange={(e) => emitAction("set_hanwha_game_idx", { idx: Number(e.target.value) })}
              >
                {hgRows.map((r, i) => (
                  <option key={`hg-${i}`} value={i}>
                    {fmtText(r.Away)} vs {fmtText(r.Home)}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
          <div className="ss-hanwha-game-actions">
            <button className="ss-primary-btn" onClick={() => emitAction("start_or_resume")}>한화 경기 시작/이어서 진행</button>
            <button className="ss-secondary-btn" onClick={() => emitAction("simulate_selected")}>한화 경기 끝까지 + 나머지 자동</button>
            <button className="ss-secondary-btn" onClick={() => emitAction("simulate_day")}>오늘 경기 전부 자동</button>
          </div>
          <SimpleTable rows={hgRows} />
        </Card>
      </div>
    );
  }

  if (screen === "standings") {
    return (
      <div className="ss-shell">
        <ScreenHeader title="순위" onBack={() => setScreen("home")} />
        <Card title="현재 리그 순위">
          <SimpleTable rows={screens?.standings || []} />
        </Card>
      </div>
    );
  }

  if (screen === "leaders") {
    return (
      <div className="ss-shell">
        <ScreenHeader title="리더보드" onBack={() => setScreen("home")} />
        <div className="ss-two-col">
          <Card title="타자 TOP">
            <SimpleTable rows={screens?.leaders?.batters || []} />
          </Card>
          <Card title="투수 TOP">
            <SimpleTable rows={screens?.leaders?.pitchers || []} />
          </Card>
        </div>
      </div>
    );
  }

  if (screen === "lineup") {
    const starters = screens?.hanwha_lineup?.starters || [];
    const bench = screens?.hanwha_lineup?.bench || [];
    return (
      <div className="ss-shell">
        <ScreenHeader title="한화 라인업" onBack={() => setScreen("home")} />
        <div className="ss-two-col">
          <Card title="선발(스타팅 9)">
            <div className="ss-lineup-list">
              {starters.map((p) => (
                <div key={`st-${p.order}-${p.name}`} className="ss-lineup-row">
                  <div className="ss-lineup-name">{p.pos} / {p.name}</div>
                  <div className="ss-lineup-meta">시즌타율 {p.avg != null ? Number(p.avg).toFixed(3) : "-"}</div>
                </div>
              ))}
            </div>
          </Card>
          <Card title="벤치">
            <div className="ss-lineup-list">
              {bench.map((p, idx) => (
                <div key={`bn-${idx}-${p.name}`} className="ss-lineup-row">
                  <div className="ss-lineup-name">{p.pos} / {p.name}</div>
                  <div className="ss-lineup-meta">시즌타율 {p.avg != null ? Number(p.avg).toFixed(3) : "-"}</div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    );
  }

  if (screen === "trade") {
    return <TradeScreen trade={screens?.trade} onBack={() => setScreen("home")} />;
  }

  if (screen === "live" && !hasLiveGame) {
    return (
      <div className="ss-shell">
        <ScreenHeader title="실시간 경기" onBack={() => setScreen("home")} />
        <NoLiveGame selectedGame={live.selected_game} />
      </div>
    );
  }

  if (screen !== "live") {
    // safety fallback
    setScreen("home");
    return null;
  }

  return (
    <div className="ss-shell">
      <ScreenHeader title="실시간 경기" onBack={() => setScreen("home")} />
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
        <div className="ss-scoreboard">
          <div className="ss-score-top">
            <div className="ss-team-side-wrap">
              <TeamLogo team={fmtText(game.away_team)} />
              <TeamLine side="AWAY" name={fmtText(game.away_team)} score={fmtText(game.score?.away, "0")} active={activeSide === "away"} />
            </div>
            <div className="ss-center-score-wrap">
              <div className="ss-center-score">{fmtText(game.score?.away, "0")} : {fmtText(game.score?.home, "0")}</div>
              <div className="ss-center-sub">{fmtText(summary.current_date)} · {fmtText(game.inning, "1")}회 {fmtText(game.half_kor)}</div>
            </div>
            <div className="ss-team-side-wrap ss-team-side-wrap-right">
              <TeamLine side="HOME" name={fmtText(game.home_team)} score={fmtText(game.score?.home, "0")} active={activeSide === "home"} />
              <TeamLogo team={fmtText(game.home_team)} />
            </div>
          </div>

          <div className="ss-chip-row">
            <Chip>{fmtText(game.inning, "1")}회 {fmtText(game.half_kor)}</Chip>
            <Chip>{fmtText(game.outs, "0")}아웃</Chip>
            <Chip>{fmtText(game.bases_text)}</Chip>
            <Chip>공격 {fmtText(game.offense_team)}</Chip>
            <Chip>수비 {fmtText(game.defense_team)}</Chip>
            <Chip>완료 경기 {fmtText(summary.completed_game_count, "0")}</Chip>
          </div>

          <div className="ss-linescore">
            <div className="ss-linescore-header">
              <div className="ss-linescore-team">팀</div>
              {Array.from({ length: maxInnings }).map((_, i) => (
                <div key={`inn-h-${i}`} className="ss-linescore-cell">{i + 1}</div>
              ))}
              <div className="ss-linescore-total">R</div>
              <div className="ss-linescore-total">H</div>
              <div className="ss-linescore-total">E</div>
              <div className="ss-linescore-total">B</div>
            </div>

            <div className={`ss-linescore-row ${activeSide === "away" ? "active" : ""}`}>
              <div className="ss-linescore-team">{fmtText(game.away_team)}</div>
              {Array.from({ length: maxInnings }).map((_, i) => (
                <div key={`away-${i}`} className="ss-linescore-cell">
                  {fmtText(lineAway[i] ?? "", "")}
                </div>
              ))}
              <div className="ss-linescore-total">{fmtText(awayTotals.R, "0")}</div>
              <div className="ss-linescore-total">{fmtText(awayTotals.H, "0")}</div>
              <div className="ss-linescore-total">{fmtText(awayTotals.E, "0")}</div>
              <div className="ss-linescore-total">{fmtText(awayTotals.B, "0")}</div>
            </div>

            <div className={`ss-linescore-row ${activeSide === "home" ? "active" : ""}`}>
              <div className="ss-linescore-team">{fmtText(game.home_team)}</div>
              {Array.from({ length: maxInnings }).map((_, i) => (
                <div key={`home-${i}`} className="ss-linescore-cell">
                  {fmtText(lineHome[i] ?? "", "")}
                </div>
              ))}
              <div className="ss-linescore-total">{fmtText(homeTotals.R, "0")}</div>
              <div className="ss-linescore-total">{fmtText(homeTotals.H, "0")}</div>
              <div className="ss-linescore-total">{fmtText(homeTotals.E, "0")}</div>
              <div className="ss-linescore-total">{fmtText(homeTotals.B, "0")}</div>
            </div>
          </div>

          <div className="ss-field-photo-wrap">
            <img src={fieldImage} alt="야구장" className="ss-field-photo" loading="lazy" />
          </div>
        </div>
      </motion.div>

      <div className="ss-main-grid ss-main-grid-live">
        <Card title="AWAY 라인업">
          <div className="ss-lineup-list">
            {(awayState?.lineup || []).map((p) => (
              <div key={`away-lineup-${p.order}-${p.name}`} className="ss-lineup-row">
                <div className="ss-lineup-name">
                  {p.pos} / {p.name}
                </div>
                <div className="ss-lineup-meta">
                  오늘타율 {p.today_avg != null ? Number(p.today_avg).toFixed(3) : "-"}
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="HOME 라인업">
          <div className="ss-lineup-list">
            {(homeState?.lineup || []).map((p) => (
              <div key={`home-lineup-${p.order}-${p.name}`} className="ss-lineup-row">
                <div className="ss-lineup-name">
                  {p.pos} / {p.name}
                </div>
                <div className="ss-lineup-meta">
                  오늘타율 {p.today_avg != null ? Number(p.today_avg).toFixed(3) : "-"}
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="감독 개입">
          <div className="ss-form-block">
            <button className="ss-primary-btn" onClick={() => emitAction("force_bunt")} disabled={!manager.can_force_bunt}>
              다음 타석 강제 번트
            </button>
          </div>

          <div className="ss-form-block">
            <div className="ss-form-label">대타</div>
            <select className="ss-select" value={phName} onChange={(e) => setPhName(e.target.value)}>
              <option value="">대타 선택</option>
              {(manager.bench_for_ph || []).map((p) => (
                <option key={p.name} value={p.name}>{p.name}</option>
              ))}
            </select>
            <button className="ss-secondary-btn" onClick={() => emitAction("apply_ph", { name: phName })} disabled={!phName}>
              대타 적용
            </button>
          </div>

          <div className="ss-form-block">
            <div className="ss-form-label">대주자</div>
            <select className="ss-select" value={prName} onChange={(e) => setPrName(e.target.value)}>
              <option value="">대주자 선택</option>
              {(manager.bench_for_pr || []).map((p) => (
                <option key={p.name} value={p.name}>{p.name}</option>
              ))}
            </select>

            <select className="ss-select" value={prBase} onChange={(e) => setPrBase(Number(e.target.value))}>
              {(manager.pr_base_choices?.length ? manager.pr_base_choices : [1]).map((b) => (
                <option key={b} value={b}>{b}루</option>
              ))}
            </select>

            <button className="ss-secondary-btn" onClick={() => emitAction("apply_pr", { name: prName, base_number: prBase })} disabled={!prName}>
              대주자 적용
            </button>
          </div>

          <div className="ss-form-block">
            <div className="ss-form-label">강제 투수 교체</div>
            <select className="ss-select" value={manualRole} onChange={(e) => setManualRole(e.target.value)}>
              <option value="">역할 선택</option>
              {(manager.eligible_manual_pitchers || []).map((role) => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
            <button className="ss-secondary-btn" onClick={() => emitAction("apply_manual_pitcher", { role: manualRole })} disabled={!manualRole}>
              강제 투수 교체 적용
            </button>
          </div>

          <div className="ss-note">현재 액션은 Python 시뮬 엔진으로 돌아가고, 이 패널은 React UI 레이어만 담당합니다.</div>
        </Card>
      </div>

      <div className="ss-bottom-grid">
        <Card title="현재 타석 매치업">
          <InfoRow label="타자" value={`${fmtText(currentBatter.name)}${currentBatter.pos ? ` / ${currentBatter.pos}` : ""}`} />
          <InfoRow label="타순" value={fmtText(currentBatter.order, "-")} />
          <InfoRow label="OPS" value={currentBatter.ops !== undefined ? Number(currentBatter.ops).toFixed(3) : "-"} />
          <InfoRow label="wRAA" value={currentBatter.wraa !== undefined ? Number(currentBatter.wraa).toFixed(1) : "-"} />
          <InfoRow label="투수" value={`${fmtText(currentPitcher.name)}${currentPitcher.role ? ` / ${currentPitcher.role}` : ""}`} />
        </Card>

        <Card title="최근 플레이 로그">
          <LogFeed lines={game.feed_display || []} />
        </Card>
      </div>
    </div>
  );
}
