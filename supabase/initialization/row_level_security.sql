--
-- Name: profiles Admin can access all table; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Admin can access all table" ON public.profiles TO service_role USING (true) WITH CHECK (true);


--
-- Name: profiles Enable ALL for users based on user_id; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Enable ALL for users based on user_id" ON public.profiles USING ((auth.uid() = id)) WITH CHECK ((auth.uid() = id));


--
-- Name: auth_sso; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_sso ENABLE ROW LEVEL SECURITY;

--
-- Name: connections; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.connections ENABLE ROW LEVEL SECURITY;

--
-- Name: groups; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.groups ENABLE ROW LEVEL SECURITY;

--
-- Name: organizations; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

--
-- Name: profiles; Type: ROW SECURITY; Schema: public; Owner: postgres
-- 

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: roles; Type: ROW SECURITY; Schema: public; Owner: postgres                                                       
--

ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;

--
-- Name: user_groups; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.user_groups ENABLE ROW LEVEL SECURITY;

--
-- Name: user_organizations; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.user_organizations ENABLE ROW LEVEL SECURITY;

--
-- Name: broadcasts; Type: ROW SECURITY; Schema: realtime; Owner: supabase_realtime_admin
--
