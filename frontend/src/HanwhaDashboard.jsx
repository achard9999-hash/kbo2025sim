import React, { useEffect, useState } from "react";
import { Streamlit } from "streamlit-component-lib";
import { motion } from "framer-motion";

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
    }, 30);
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

export default function HanwhaDashboard(props) {
  const appPayload = props.args?.appPayload || {};
  const live = appPayload.live_game || {};
  const game = live.game_state || null;
  const manager = live.manager_actions || {};
  const summary = appPayload.season_summary || {};

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

  useAutoHeight([
    hasLiveGame,
    game?.inning,
    game?.half,
    game?.outs,
    game?.score?.away,
    game?.score?.home,
    game?.feed_display?.length,
    phName,
    prName,
    prBase,
    manualRole,
  ]);

  if (!hasLiveGame) {
    return <NoLiveGame selectedGame={live.selected_game} />;
  }

  return (
    <div className="ss-shell">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
        <div className="ss-scoreboard">
          <div className="ss-score-top">
            <TeamLine side="AWAY" name={fmtText(game.away_team)} score={fmtText(game.score?.away, "0")} active={activeSide === "away"} />
            <div className="ss-center-score-wrap">
              <div className="ss-center-score">{fmtText(game.score?.away, "0")} : {fmtText(game.score?.home, "0")}</div>
              <div className="ss-center-sub">{fmtText(summary.current_date)} · {fmtText(game.inning, "1")}회 {fmtText(game.half_kor)}</div>
            </div>
            <TeamLine side="HOME" name={fmtText(game.home_team)} score={fmtText(game.score?.home, "0")} active={activeSide === "home"} />
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
              {Array.from({ length: 9 }).map((_, i) => (
                <div key={`inn-h-${i}`} className="ss-linescore-cell">{i + 1}</div>
              ))}
              <div className="ss-linescore-total">R</div>
            </div>

            <div className={`ss-linescore-row ${activeSide === "away" ? "active" : ""}`}>
              <div className="ss-linescore-team">{fmtText(game.away_team)}</div>
              {lineAway.map((v, i) => (
                <div key={`away-${i}`} className="ss-linescore-cell">{fmtText(v, "")}</div>
              ))}
              <div className="ss-linescore-total">{fmtText(game.score?.away, "0")}</div>
            </div>

            <div className={`ss-linescore-row ${activeSide === "home" ? "active" : ""}`}>
              <div className="ss-linescore-team">{fmtText(game.home_team)}</div>
              {lineHome.map((v, i) => (
                <div key={`home-${i}`} className="ss-linescore-cell">{fmtText(v, "")}</div>
              ))}
              <div className="ss-linescore-total">{fmtText(game.score?.home, "0")}</div>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="ss-main-grid">
        <Card title="경기 상황">
          <div className="ss-field-panel">
            <div className="ss-field-inner">
              <div className="ss-field-grass" />
              <div className="ss-field-diamond" />
              <div className="ss-pitcher-mound" />
              <BaseDiamond active={base2} label="2루" />
              <div className="ss-bases-row">
                <BaseDiamond active={base1} label="1루" />
                <BaseDiamond active={base3} label="3루" />
              </div>
            </div>
          </div>

          <InfoRow label="공격 팀" value={fmtText(game.offense_team)} />
          <InfoRow label="수비 팀" value={fmtText(game.defense_team)} />
          <InfoRow label="다음 타자" value={fmtText(currentBatter.name)} />
          <InfoRow label="현재 투수" value={`${fmtText(currentPitcher.name)}${currentPitcher.role ? ` (${currentPitcher.role})` : ""}`} />
          <InfoRow label="주자 상황" value={fmtText(game.bases_text)} />

          <div className="ss-action-grid">
            <button className="ss-primary-btn" onClick={() => emitAction("live_pa")}>1타석 진행</button>
            <button className="ss-secondary-btn" onClick={() => emitAction("live_half")}>반이닝 진행</button>
            <button className="ss-secondary-btn" onClick={() => emitAction("simulate_selected")}>경기 끝까지 진행</button>
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
