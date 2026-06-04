/* eslint-disable */
/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */
/** @typedef {{}} App_NameInputs */
/** @typedef {{}} Nav_HomeInputs */
/** @typedef {{}} Nav_SearchInputs */
/** @typedef {{}} Nav_MessagesInputs */
/** @typedef {{}} Nav_AppsInputs */
/** @typedef {{}} Nav_ProfileInputs */
/** @typedef {{}} Drawer_CreditsInputs */
/** @typedef {{}} Drawer_MurakumoInputs */
/** @typedef {{}} Drawer_Hc_TasksInputs */
/** @typedef {{}} Drawer_TermsInputs */
/** @typedef {{}} Drawer_PrivacyInputs */
/** @typedef {{}} Drawer_FeedbackInputs */
/** @typedef {{}} Drawer_HelpInputs */
/** @typedef {{}} Drawer_HistoryInputs */
/** @typedef {{}} Drawer_SettingsInputs */
/** @typedef {{}} Drawer_Sign_OutInputs */
/** @typedef {{}} Cookie_TitleInputs */
/** @typedef {{}} Cookie_DescriptionInputs */
/** @typedef {{}} Cookie_DeclineInputs */
/** @typedef {{}} Cookie_AcceptInputs */
/** @typedef {{}} Inference_Important_NoticeInputs */
/** @typedef {{}} Inference_Scroll_PromptInputs */
/** @typedef {{}} Inference_Agree_CheckboxInputs */
/** @typedef {{}} Inference_DeclineInputs */
/** @typedef {{}} Inference_AgreeInputs */
/** @typedef {{}} Content_Label_BackInputs */
/** @typedef {{}} Content_Label_AgreeInputs */
/** @typedef {{}} Profile_Spam_BlockInputs */
/** @typedef {{ threshold: NonNullable<unknown> }} Profile_Spam_Block_DescInputs */
/** @typedef {{}} Profile_PostsInputs */
/** @typedef {{}} Profile_FollowersInputs */
/** @typedef {{}} Profile_FollowingInputs */
/** @typedef {{}} Profile_FollowInputs */
/** @typedef {{}} Profile_UnfollowInputs */
/** @typedef {{}} Profile_MessageInputs */
/** @typedef {{}} Profile_EditInputs */
/** @typedef {{}} Search_ActorsInputs */
/** @typedef {{}} Search_PostsInputs */
/** @typedef {{}} Search_PeopleInputs */
/** @typedef {{}} Search_PlaceholderInputs */
/** @typedef {{}} Feed_DiscoverInputs */
/** @typedef {{}} Feed_FollowingInputs */
/** @typedef {{}} Feed_EmptyInputs */
/** @typedef {{}} Feed_LoadingInputs */
/** @typedef {{}} Feed_Error_RetryInputs */
/** @typedef {{}} Compose_PlaceholderInputs */
/** @typedef {{}} Compose_PostInputs */
/** @typedef {{}} Compose_CancelInputs */
/** @typedef {{}} Convo_New_MessageInputs */
/** @typedef {{}} Convo_EmptyInputs */
/** @typedef {{}} Common_LoadingInputs */
/** @typedef {{}} Common_ErrorInputs */
/** @typedef {{}} Common_RetryInputs */
/** @typedef {{}} Common_SaveInputs */
/** @typedef {{}} Common_CancelInputs */
/** @typedef {{}} Common_DeleteInputs */
/** @typedef {{}} Common_ConfirmInputs */
/** @typedef {{}} Common_BackInputs */
/** @typedef {{}} Common_CloseInputs */
/** @typedef {{ count: NonNullable<unknown> }} Common_ViewsInputs */


export const app_name = /** @type {(inputs: App_NameInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`YORO`)
};

export const nav_home = /** @type {(inputs: Nav_HomeInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ହୋମ`)
};

export const nav_search = /** @type {(inputs: Nav_SearchInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଖୋଜ`)
};

export const nav_messages = /** @type {(inputs: Nav_MessagesInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ସନ୍ଦେଶ`)
};

export const nav_apps = /** @type {(inputs: Nav_AppsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଆପ୍ସ`)
};

export const nav_profile = /** @type {(inputs: Nav_ProfileInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ପ୍ରୋଫାଇଲ`)
};

export const drawer_credits = /** @type {(inputs: Drawer_CreditsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`କ୍ରେଡିଟ`)
};

export const drawer_murakumo = /** @type {(inputs: Drawer_MurakumoInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Murakumo`)
};

export const drawer_hc_tasks = /** @type {(inputs: Drawer_Hc_TasksInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`HC କାର୍ଯ୍ୟ`)
};

export const drawer_terms = /** @type {(inputs: Drawer_TermsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ବ୍ୟବହାର ସର୍ତ୍ତ`)
};

export const drawer_privacy = /** @type {(inputs: Drawer_PrivacyInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଗୋପନୀୟତା ନୀତି`)
};

export const drawer_feedback = /** @type {(inputs: Drawer_FeedbackInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ମତାମତ`)
};

export const drawer_help = /** @type {(inputs: Drawer_HelpInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ସାହାଯ୍ୟ`)
};

export const drawer_history = /** @type {(inputs: Drawer_HistoryInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ବ୍ରାଉଜିଂ ଇତିହାସ`)
};

export const drawer_settings = /** @type {(inputs: Drawer_SettingsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ସେଟିଂସ`)
};

export const drawer_sign_out = /** @type {(inputs: Drawer_Sign_OutInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ସାଇନ୍ ଆଉଟ୍`)
};

export const cookie_title = /** @type {(inputs: Cookie_TitleInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`କୁକି`)
};

export const cookie_description = /** @type {(inputs: Cookie_DescriptionInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`YORO ସମ୍ବନ୍ଧିତ ବିଜ୍ଞାପନ ଦେଖାଇବା ପାଇଁ କୁକି ବ୍ୟବହାର କରେ।`)
};

export const cookie_decline = /** @type {(inputs: Cookie_DeclineInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ପ��ରତ୍ୟାଖ��ୟାନ`)
};

export const cookie_accept = /** @type {(inputs: Cookie_AcceptInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଗ୍ରହଣ`)
};

export const inference_important_notice = /** @type {(inputs: Inference_Important_NoticeInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଇନ୍ଫରେନ୍ସ ଅଂଶଗ୍ରହଣ ବିଷୟରେ ଗୁରୁତ୍ୱପୂର୍ଣ୍ଣ ସୂଚନା`)
};

export const inference_scroll_prompt = /** @type {(inputs: Inference_Scroll_PromptInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଦୟାକରି ତଳକୁ ସ୍କ୍ରୋଲ କରନ୍ତୁ`)
};

export const inference_agree_checkbox = /** @type {(inputs: Inference_Agree_CheckboxInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ମୁଁ ଉପରୋକ୍ତ ସମସ୍ତ ସର୍ତ୍ତ ପଢ଼ିଛି, ବୁଝିଛି ଏବଂ ସ୍ୱୀକାର କରୁଛି।`)
};

export const inference_decline = /** @type {(inputs: Inference_DeclineInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ପ୍ରତ୍ୟାଖ୍ୟାନ`)
};

export const inference_agree = /** @type {(inputs: Inference_AgreeInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ସମ୍ମତ ଏବଂ ଯୋଗ ଦିଅନ୍ତୁ`)
};

export const content_label_back = /** @type {(inputs: Content_Label_BackInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ପଛକୁ`)
};

export const content_label_agree = /** @type {(inputs: Content_Label_AgreeInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ମୁଁ ଉପରୋକ୍ତ ସହ ସମ���ମତ`)
};

export const profile_spam_block = /** @type {(inputs: Profile_Spam_BlockInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ସ୍ପାମ ବ୍ଲକ`)
};

export const profile_spam_block_desc = /** @type {(inputs: Profile_Spam_Block_DescInputs) => LocalizedString} */ (i) => {
	return /** @type {LocalizedString} */ (`${i?.threshold} ରୁ କମ ସ୍ୱତଃ ପ୍ରତ୍ୟାଖ୍ୟାନ`)
};

export const profile_posts = /** @type {(inputs: Profile_PostsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ପୋଷ୍ଟ`)
};

export const profile_followers = /** @type {(inputs: Profile_FollowersInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଅନୁସରଣକାରୀ`)
};

export const profile_following = /** @type {(inputs: Profile_FollowingInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଅନୁସରଣ`)
};

export const profile_follow = /** @type {(inputs: Profile_FollowInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଅନୁସରଣ`)
};

export const profile_unfollow = /** @type {(inputs: Profile_UnfollowInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଅନଫଲୋ`)
};

export const profile_message = /** @type {(inputs: Profile_MessageInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ସନ୍ଦେଶ`)
};

export const profile_edit = /** @type {(inputs: Profile_EditInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ପ୍ରୋଫାଇଲ ସମ୍ପାଦନ`)
};

export const search_actors = /** @type {(inputs: Search_ActorsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଆକ୍ଟର`)
};

export const search_posts = /** @type {(inputs: Search_PostsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ପୋଷ୍ଟ`)
};

export const search_people = /** @type {(inputs: Search_PeopleInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଲୋକ`)
};

export const search_placeholder = /** @type {(inputs: Search_PlaceholderInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`YORO ରେ ଖୋଜନ୍ତୁ`)
};

export const feed_discover = /** @type {(inputs: Feed_DiscoverInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଆବିଷ୍କାର`)
};

export const feed_following = /** @type {(inputs: Feed_FollowingInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଅନୁସରଣ`)
};

export const feed_empty = /** @type {(inputs: Feed_EmptyInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଏପର୍ଯ୍ୟନ୍ତ ପୋଷ୍ଟ ନାହିଁ`)
};

export const feed_loading = /** @type {(inputs: Feed_LoadingInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଲୋଡ ହେଉଛି...`)
};

export const feed_error_retry = /** @type {(inputs: Feed_Error_RetryInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ପୁଣି ଚେଷ୍ଟା`)
};

export const compose_placeholder = /** @type {(inputs: Compose_PlaceholderInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`କଣ ହେଉଛି?`)
};

export const compose_post = /** @type {(inputs: Compose_PostInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ପୋଷ୍ଟ`)
};

export const compose_cancel = /** @type {(inputs: Compose_CancelInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ବାତିଲ`)
};

export const convo_new_message = /** @type {(inputs: Convo_New_MessageInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ନୂଆ ସନ୍ଦେଶ`)
};

export const convo_empty = /** @type {(inputs: Convo_EmptyInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଏପର୍ଯ୍ୟନ୍ତ ସଂଭାଷଣ ନାହିଁ`)
};

export const common_loading = /** @type {(inputs: Common_LoadingInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ଲୋଡ ହେଉଛି...`)
};

export const common_error = /** @type {(inputs: Common_ErrorInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`କିଛି ଭୁଲ ହୋଇଗଲା`)
};

export const common_retry = /** @type {(inputs: Common_RetryInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ପୁଣି ଚେଷ୍ଟା`)
};

export const common_save = /** @type {(inputs: Common_SaveInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ସେଭ`)
};

export const common_cancel = /** @type {(inputs: Common_CancelInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ବାତିଲ`)
};

export const common_delete = /** @type {(inputs: Common_DeleteInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ବିଲୋପ`)
};

export const common_confirm = /** @type {(inputs: Common_ConfirmInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ନିଶ୍ଚିତ`)
};

export const common_back = /** @type {(inputs: Common_BackInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ପଛକୁ`)
};

export const common_close = /** @type {(inputs: Common_CloseInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ବନ���ଦ`)
};

export const common_views = /** @type {(inputs: Common_ViewsInputs) => LocalizedString} */ (i) => {
	return /** @type {LocalizedString} */ (`${i?.count} ଦର୍ଶନ`)
};