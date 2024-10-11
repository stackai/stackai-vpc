--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
-- 

INSERT INTO public.roles (id, created_at, name, view_projects, edit_projects, invite_users, remove_users, export_flows, edit_roles)
VALUES 
('4a325d88-a6d0-40e6-b59c-c375acba5d48', '2024-01-04 03:21:40.659019+00', 'admin', true, true, true, true, true, true),
('4536a662-8470-4690-9c82-cfb608ab1b70', '2024-01-04 03:22:06.225862+00', 'viewer', true, false, false, false, false, false),
('74f1a168-d409-4888-aeeb-fce2d1ee7df4', '2024-02-22 01:30:58.317801+00', 'editor', true, true, false, false, true, false),
('4139659e-766a-4e7b-9b5f-82544a781b6a', '2024-03-13 00:31:02.462615+00', 'user', false, false, false, false, false, false);





--- Data for storage.buckets ---
INSERT INTO storage.buckets (id, name, owner, created_at, updated_at)
VALUES
('assistant-avatars', 'assistant-avatars', null, '2024-03-13 19:56:18.429791+00', '2024-03-13 19:56:18.429791+00'),
('avatars', 'avatars', null, '2023-01-11 18:19:09.555934+00', '2023-01-11 18:19:09.555934+00'),
('chat-assistant-vision', 'chat-assistant-vision', null, '2024-07-18 13:17:53.339888+00', '2024-07-18 13:17:53.339888+00'),
('dataframes', 'dataframes', null, '2023-06-17 00:28:06.036874+00', '2023-06-17 00:28:06.036874+00'),
('document_libraries', 'document_libraries', null, '2023-05-22 00:57:43.723831+00', '2023-05-22 00:57:43.723831+00'),
('documents', 'documents', null, '2023-03-20 03:51:44.487984+00', '2023-03-20 03:51:44.487984+00'),
('flow-screenshots', 'flow-screenshots', null, '2023-03-30 07:50:00.723077+00', '2023-03-30 07:50:00.723077+00'),
('indexed_documents', 'indexed_documents', null, '2023-05-02 21:23:31.961262+00', '2023-05-02 21:23:31.961262+00'),
('indexed_tables', 'indexed_tables', null, '2023-09-20 15:23:37.81324+00', '2023-09-20 15:23:37.81324+00'),
('kb_vfs_indexed_documents', 'kb_vfs_indexed_documents', null, '2024-05-17 19:19:51.964184+00', '2024-05-17 19:19:51.964184+00'),
('screenshots', 'screenshots', null, '2023-01-13 23:01:26.210083+00', '2023-01-13 23:01:26.210083+00'),
('temporary_cdn', 'temporary_cdn', null, '2024-09-05 10:20:09.743622+00', '2024-09-05 10:20:09.743622+00'),
('user_documents', 'user_documents', null, '2023-06-24 02:20:26.927197+00', '2023-06-24 02:20:26.927197+00');