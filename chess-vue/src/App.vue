<template>
  <div id="app">
    <h3>{{ boardStr }}</h3>

    <div id="MaxBox">
      <div v-for="y in 4" :key="y - 1" class="line">
        <m-piece
          v-for="x in rangeX"
          :key="x"
          v-bind="pieceArgs"
          :x="x"
          :y="y - 1"
          @click.native="onPieceClick(x, y - 1)"
        />
      </div>

      <div class="line river1">
        <m-piece
          v-for="x in rangeX"
          :key="x"
          v-bind="pieceArgs"
          :x="x"
          :y="4"
          @click.native="onPieceClick(x, 4)"
        />
      </div>

      <div class="boxCenter">
        <div class="boxCenterLeft">河<br /><br />界</div>
        <div class="boxCenterRight">河<br /><br />界</div>
      </div>

      <div class="line river2">
        <m-piece
          v-for="x in rangeX"
          :key="x"
          v-bind="pieceArgs"
          :x="x"
          :y="5"
          @click.native="onPieceClick(x, 5)"
        />
      </div>

      <div v-for="y in 4" :key="y + 5" class="line">
        <m-piece
          v-for="x in rangeX"
          :key="x"
          v-bind="pieceArgs"
          :x="x"
          :y="y + 5"
          @click.native="onPieceClick(x, y + 5)"
        />
      </div>
    </div>
    <h4 v-if="humanSideText" :style="humanSideStyle">
      人：{{ humanSideText }}
      <span v-if="activePiece">选中棋子：{{ activePiece }}</span>
      <span v-if="processing">（正在思考...）</span>
    </h4>
  </div>
</template>

<script>
const axios = require("axios").default.create({});

const NUMBERS = "0123456789";
const ALPHABET = "abcdefghi";

import Piece from "./components/Piece";

export default {
  name: "App",
  components: { "m-piece": Piece },
  data() {
    return {
      rangeX: [0, 1, 2, 3, 4, 5, 6, 7, 8],
      board: [],
      boardStr: "9/9/9/9/9/9/9/9/9/9",
      active: null,
      gameId: null,
      validMoves: [],
      humanSide: null,
      netSide: null,
      processing: false,
      lastMove: "",
    };
  },
  methods: {
    initCanvas() {
      var els = document.getElementsByClassName("myCanvas");
      for (let i = 0; i < els.length; i++) {
        let cxt = els[i].getContext("2d");
        cxt.beginPath();
        cxt.moveTo(0, 0);
        cxt.lineTo(44.25, 44.25);
        cxt.rotate(900);
        cxt.stroke();
      }

      var els2 = document.getElementsByClassName("myCanvas2");
      for (let i = 0; i < els2.length; i++) {
        let cxt = els2[i].getContext("2d");
        cxt.beginPath();
        cxt.moveTo(44.25, 0);
        cxt.lineTo(0, 44.25);
        cxt.rotate(900);
        cxt.stroke();
      }
    },
    onPieceClick(x, y) {
      if (this.processing) {
        return;
      }
      if (this.active) {
        if (this.active[0] == x && this.active[1] == y) {
          // Deactivate
          this.active = null;
          return;
        }

        for (const cord of this.activeValidTarget) {
          if (cord[0] === x && cord[1] === y) {
            this.remoteDoMove(this.active[0], this.active[1], x, y);
            return;
          }
        }
      }

      if (this.board[y][x] !== null) {
        // Activate
        this.active = [x, y];
        return;
      }
    },
    async initGame() {
      this.processing = true;
      try {
        const response = await axios.post("/game");
        this.loadResponse(response);
      } catch (error) {
        alert(error);
      } finally {
        this.processing = false;
      }
    },
    loadResponse(response) {
      if (response.data.end) {
        alert("Winner: " + response.data.end === "b" ? "黑" : "红");
        this.initGame();
        return;
      }
      this.boardStr = response.data.state;
      this.gameId = response.data.id;
      this.validMoves = response.data.validMoves;
      this.humanSide = response.data.humanSide;
      this.netSide = response.data.netSide;
      this.lastMove = response.data.lastMove;
    },
    coordToFen(x, y) {
      return `${ALPHABET[x]}${NUMBERS[y]}`;
    },
    fenToCoord(fen) {
      return [ALPHABET.indexOf(fen[0]), NUMBERS.indexOf(fen[1])];
    },
    async remoteDoMove(sx, sy, dx, dy) {
      const from = this.coordToFen(sx, sy);
      const to = this.coordToFen(dx, dy);
      const move = from + to;

      this.$set(this.board[dy], dx, this.board[sy][sx]);
      this.$set(this.board[sy], sx, null);

      this.active = null;

      const bodyFormData = new FormData();
      bodyFormData.append("uuid", this.gameId);
      bodyFormData.append("move", move);

      try {
        this.processing = true;
        const response = await axios.post("/game/interact", bodyFormData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        this.loadResponse(response);
      } catch (error) {
        alert(error);
      } finally {
        this.processing = false;
      }
    },
  },

  computed: {
    pieceArgs() {
      return {
        board: this.board,
        active: this.active,
        targets: this.activeValidTarget,
        lastMoveCoords: this.lastMoveCoords,
      };
    },
    activePiece() {
      if (!this.active) {
        return null;
      }
      return this.coordToFen(this.active[0], this.active[1]);
    },
    activeValidTarget() {
      if (!this.activePiece || !this.validMoves) {
        return [];
      }

      let ret = [];
      for (const move of this.validMoves) {
        if (move.startsWith(this.activePiece)) {
          ret.push(this.fenToCoord(move.substring(2)));
        }
      }

      return ret;
    },
    humanSideText() {
      if (this.humanSide === "b") {
        return "黑";
      } else if (this.humanSide === "w") {
        return "红";
      } else {
        return null;
      }
    },
    humanSideStyle() {
      if (this.humanSide === "b") {
        return { color: "black" };
      } else if (this.humanSide === "w") {
        return { color: "red" };
      } else {
        return { color: "black" };
      }
    },
    lastMoveCoords() {
      if (!this.lastMove) {
        return [];
      }
      return [
        this.fenToCoord(this.lastMove.substring(0, 2)),
        this.fenToCoord(this.lastMove.substring(2)),
      ];
    },
  },

  mounted() {
    this.initCanvas();
    this.initGame();
  },

  watch: {
    boardStr: {
      immediate: true,
      handler(fenStr) {
        let board = [[]];
        let currentRow = board[0];

        for (let ch of fenStr) {
          if (ch === "/") {
            currentRow = [];
            board.push(currentRow);
          } else if (NUMBERS.indexOf(ch) !== -1) {
            let num = parseInt(ch, 10);
            for (let index = 0; index < num; index++) {
              currentRow.push(null);
            }
          } else {
            currentRow.push(ch);
          }
        }

        this.board = board;
      },
    },
  },
};
</script>

<style lang="scss">
@import "./assets/app.css";

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
