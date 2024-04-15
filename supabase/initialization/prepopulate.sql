--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
-- 

INSERT INTO public.roles (id, created_at, name, view_projects, edit_projects, invite_users, remove_users, export_flows, edit_roles)
VALUES 
('4a325d88-a6d0-40e6-b59c-c375acba5d48', '2024-01-04 03:21:40.659019+00', 'admin', true, true, true, true, true, true),
('4536a662-8470-4690-9c82-cfb608ab1b70', '2024-01-04 03:22:06.225862+00', 'viewer', true, false, false, false, false, false),
('74f1a168-d409-4888-aeeb-fce2d1ee7df4', '2024-02-22 01:30:58.317801+00', 'editor', true, true, false, false, true, false),
('4139659e-766a-4e7b-9b5f-82544a781b6a', '2024-03-13 00:31:02.462615+00', 'user', false, false, false, false, false, false);
