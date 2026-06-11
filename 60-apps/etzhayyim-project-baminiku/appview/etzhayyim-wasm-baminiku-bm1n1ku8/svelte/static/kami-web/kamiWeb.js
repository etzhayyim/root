// Shim: re-export wasm-bindgen snake_case exports as camelCase aliases
// expected by @etzhayyim/kami-engine-sdk builders/createVrmEngine.svelte.ts.
import initCore, * as core from './kamiWebCore.js';

export default initCore;

export const runEmbedVrm = core.run_embed_vrm;
export const getVrmMorphNames = core.get_vrm_morph_names;
export const getVrmSkeletonInfo = core.get_vrm_skeleton_info;
export const getVrmBoneNames = core.get_vrm_bone_names;
export const setVrmMorph = core.set_vrm_morph;
export const setVrmMorphByName = core.set_vrm_morph_by_name;
export const resetVrmMorphs = core.reset_vrm_morphs;
export const setVrmCamera = core.set_vrm_camera;
export const setVrmBoneRotation = core.set_vrm_bone_rotation;
export const resetVrmPose = core.reset_vrm_pose;
export const evaluateMotion = core.evaluate_motion;
export const clampBone = core.clamp_bone;
export const getVrmMeshLabels = core.get_vrm_mesh_labels;
export const setVrmMeshVisibility = core.set_vrm_mesh_visibility;
export const composeVrmWithPreset = core.compose_vrm_with_preset;
