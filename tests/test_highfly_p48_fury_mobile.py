import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import highfly_p48_fury_mobile as p
class Tests(unittest.TestCase):
 def fixture(self):
  return {
   p.FILES[0]:("    const inAutorunTarget = isMoveAutorunPush(rawY);\n"
     "    this.input.setAutorun(true);\n"
     "    this.syncMoveAutorunTarget(isMoveAutorunNear(rawY) ? 'near' : 'hidden');\n"
     "    this.bindButton('mobile-jump', () => this.callbacks.onJump(), { pressFirst: true });"),
   p.FILES[1]:("  autorun = false;\n  suspendMovement = false;\n"
     "  /** Touch/controller swim-down, held for as long as the control is pressed. */\n"
     "    this.touchJumpUntil = 0;\n    this.autorun = false;\n"
     "      performance.now() <= this.keyJumpUntil;\n"
     "        jump,\n        dive,\n        surface,\n"
     "      jump,\n      dive,\n      surface,"),
   p.FILES[2]:"  jump: boolean;\n  /** Swim DOWN.",
   p.FILES[3]:("export const AIR_CONTROL_ACCEL = 20;\n"
     "  const movingOnGround = moving && (p.onGround || swimming);\n"
     "  if (inp.jump && (p.onGround || coyote) && !isRooted(p) && !steepGround && !mountLocked) {\n"
     "    p.vy = JUMP_VELOCITY * jumpMult(p);"),
   p.FILES[4]:("      (proneAngle + swimPitch) * this.swimBlend + this.lean + CLIMB_BODY_PITCH * climb * climbLevel;\n"
     "        this.climbHeadBone.rotation.x += CLIMB_HEAD_TILT_RAD * look * this.climbBlend;\n"
     "      this.climbHeadBone.rotation.x += CLIMB_HEAD_TILT_RAD * look * k;"),
   p.FILES[5]:('<head></head>\n'
     '<button type="button" id="mobile-jump" data-i18n-title=')
  }
 def test_true_mobile_movement_no_autorun(self):
  out=p.patch(self.fixture())
  self.assertNotIn("isMoveAutorunPush(rawY)",out[p.FILES[0]])
  self.assertIn("this.input.triggerTouchDash()",out[p.FILES[0]])
  self.assertIn("const furyDashing =",out[p.FILES[3]])
  self.assertIn("highflyAirJumps",out[p.FILES[3]])
  self.assertIn("freshJump",out[p.FILES[3]])
  self.assertIn("dash?: boolean",out[p.FILES[2]])
  self.assertIn("id=\"mobile-dodge\"",out[p.FILES[5]])
 def test_loading_native_bar_not_fake(self):
  self.assertIn("#loading-screen #ls-fill",p.CSS)
  self.assertNotIn("setInterval",p.JS)
  self.assertIn("highfly_splash.png",p.CSS)
  self.assertIn("fullscreen",p.JS)
 def test_reapply_safety(self):
  z=p.patch(self.fixture())
  with self.assertRaisesRegex(RuntimeError,"P48_ALREADY_APPLIED"):
   p.patch(z)
 def test_anchor_drift(self):
  z=self.fixture();z[p.FILES[1]]="other"
  with self.assertRaisesRegex(RuntimeError,"P48_ANCHOR_DRIFT"):
   p.patch(z)
if __name__=="__main__":unittest.main()
