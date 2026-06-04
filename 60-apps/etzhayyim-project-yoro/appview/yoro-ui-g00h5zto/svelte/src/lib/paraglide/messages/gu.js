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
	return /** @type {LocalizedString} */ (`હોમ`)
};

export const nav_search = /** @type {(inputs: Nav_SearchInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`શોધો`)
};

export const nav_messages = /** @type {(inputs: Nav_MessagesInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`સંદેશા`)
};

export const nav_apps = /** @type {(inputs: Nav_AppsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`એપ્સ`)
};

export const nav_profile = /** @type {(inputs: Nav_ProfileInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`પ્રોફાઇલ`)
};

export const drawer_credits = /** @type {(inputs: Drawer_CreditsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ક્રેડિટ્સ`)
};

export const drawer_murakumo = /** @type {(inputs: Drawer_MurakumoInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Murakumo`)
};

export const drawer_hc_tasks = /** @type {(inputs: Drawer_Hc_TasksInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`HC કાર્ય`)
};

export const drawer_terms = /** @type {(inputs: Drawer_TermsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ઉપયોગની શરતો`)
};

export const drawer_privacy = /** @type {(inputs: Drawer_PrivacyInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ગોપનીયતા નીતિ`)
};

export const drawer_feedback = /** @type {(inputs: Drawer_FeedbackInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`પ્રતિસાદ`)
};

export const drawer_help = /** @type {(inputs: Drawer_HelpInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`મદદ`)
};

export const drawer_history = /** @type {(inputs: Drawer_HistoryInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`બ્રાઉઝિંગ ઇતિહાસ`)
};

export const drawer_settings = /** @type {(inputs: Drawer_SettingsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`સેટિંગ્સ`)
};

export const drawer_sign_out = /** @type {(inputs: Drawer_Sign_OutInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`સાઇન આઉટ`)
};

export const cookie_title = /** @type {(inputs: Cookie_TitleInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`કૂકીઝ`)
};

export const cookie_description = /** @type {(inputs: Cookie_DescriptionInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`YORO Google AdSense અને પાર્ટનર નેટવર્ક્સ દ્વારા સંબંધિત જાહેરાતો બતાવવા કૂકીઝનો ઉપયોગ કરે છે.`)
};

export const cookie_decline = /** @type {(inputs: Cookie_DeclineInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`નકારો`)
};

export const cookie_accept = /** @type {(inputs: Cookie_AcceptInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`સ્વીકારો`)
};

export const inference_important_notice = /** @type {(inputs: Inference_Important_NoticeInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ઇન્ફરન્સ ભાગીદારી વિશે મહત્વપૂર્ણ સૂચના`)
};

export const inference_scroll_prompt = /** @type {(inputs: Inference_Scroll_PromptInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`કૃપા કરીને નીચે સુધી સ્ક્રોલ કરો`)
};

export const inference_agree_checkbox = /** @type {(inputs: Inference_Agree_CheckboxInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`મેં ઉપરની બધી શરતો વાંચી, સમજી અને સ્વીકારી.`)
};

export const inference_decline = /** @type {(inputs: Inference_DeclineInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`નકારો`)
};

export const inference_agree = /** @type {(inputs: Inference_AgreeInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`સંમત થાઓ અને ભાગ લો`)
};

export const content_label_back = /** @type {(inputs: Content_Label_BackInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`પાછળ`)
};

export const content_label_agree = /** @type {(inputs: Content_Label_AgreeInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`હું ઉપરોક્ત સાથે સંમત છું`)
};

export const profile_spam_block = /** @type {(inputs: Profile_Spam_BlockInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`સ્પેમ બ્લોક`)
};

export const profile_spam_block_desc = /** @type {(inputs: Profile_Spam_Block_DescInputs) => LocalizedString} */ (i) => {
	return /** @type {LocalizedString} */ (`${i?.threshold} કરતાં ઓછો સ્કોર આપમેળે નકારો`)
};

export const profile_posts = /** @type {(inputs: Profile_PostsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`પોસ્ટ્સ`)
};

export const profile_followers = /** @type {(inputs: Profile_FollowersInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ફૉલોઅર્સ`)
};

export const profile_following = /** @type {(inputs: Profile_FollowingInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ફૉલોઇંગ`)
};

export const profile_follow = /** @type {(inputs: Profile_FollowInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ફૉલો`)
};

export const profile_unfollow = /** @type {(inputs: Profile_UnfollowInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`અનફૉલો`)
};

export const profile_message = /** @type {(inputs: Profile_MessageInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`સંદેશ`)
};

export const profile_edit = /** @type {(inputs: Profile_EditInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`પ્રોફાઇલ સંપાદિત કરો`)
};

export const search_actors = /** @type {(inputs: Search_ActorsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`એક્ટર્સ`)
};

export const search_posts = /** @type {(inputs: Search_PostsInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`પોસ્ટ્સ`)
};

export const search_people = /** @type {(inputs: Search_PeopleInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`લોકો`)
};

export const search_placeholder = /** @type {(inputs: Search_PlaceholderInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`YORO માં શોધો`)
};

export const feed_discover = /** @type {(inputs: Feed_DiscoverInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`શોધો`)
};

export const feed_following = /** @type {(inputs: Feed_FollowingInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ફૉલોઇંગ`)
};

export const feed_empty = /** @type {(inputs: Feed_EmptyInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`હજી કોઈ પોસ્ટ નથી`)
};

export const feed_loading = /** @type {(inputs: Feed_LoadingInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`લોડ થઈ રહ્યું છે...`)
};

export const feed_error_retry = /** @type {(inputs: Feed_Error_RetryInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ફરી પ્રયાસ કરો`)
};

export const compose_placeholder = /** @type {(inputs: Compose_PlaceholderInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`શું ચાલે છે?`)
};

export const compose_post = /** @type {(inputs: Compose_PostInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`પોસ્ટ`)
};

export const compose_cancel = /** @type {(inputs: Compose_CancelInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`રદ કરો`)
};

export const convo_new_message = /** @type {(inputs: Convo_New_MessageInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`નવો સંદેશ`)
};

export const convo_empty = /** @type {(inputs: Convo_EmptyInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`હજી કોઈ વાતચીત નથી`)
};

export const common_loading = /** @type {(inputs: Common_LoadingInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`લોડ થઈ રહ્યું છે...`)
};

export const common_error = /** @type {(inputs: Common_ErrorInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`કંઈક ખોટું થયું`)
};

export const common_retry = /** @type {(inputs: Common_RetryInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ફરી પ્રયાસ કરો`)
};

export const common_save = /** @type {(inputs: Common_SaveInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`સેવ`)
};

export const common_cancel = /** @type {(inputs: Common_CancelInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`રદ કરો`)
};

export const common_delete = /** @type {(inputs: Common_DeleteInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`ડિલીટ`)
};

export const common_confirm = /** @type {(inputs: Common_ConfirmInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`પુષ્ટિ`)
};

export const common_back = /** @type {(inputs: Common_BackInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`પાછળ`)
};

export const common_close = /** @type {(inputs: Common_CloseInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`બંધ`)
};

export const common_views = /** @type {(inputs: Common_ViewsInputs) => LocalizedString} */ (i) => {
	return /** @type {LocalizedString} */ (`${i?.count} વ્યૂઝ`)
};